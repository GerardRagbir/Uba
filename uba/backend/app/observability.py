"""Logs, metrics and request IDs: how we see what the running app is doing.

- Logs    : one JSON object per line on stdout. Docker collects them.
- Metrics : numbers Prometheus scrapes from /metrics every few seconds.
- Request ID : one ID per request, in every log line and in the response
               header, so a single request can be followed through the logs.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# ---------- metrics ----------
#
# There are four kinds of metric on show here, and the dashboard is built
# around the difference:
#   Counter   - only ever goes up (total requests, total logins). You chart
#               its *rate*: rate(...[5m]) = "per second, lately".
#   Gauge     - goes up and down (requests in flight right now, bookings
#               currently pending). You chart its value.
#   Histogram - buckets of observations (how long requests took, how big
#               fares were). It lets you ask for a percentile later.

# --- "is the server up and fast?" (technical / RED metrics) ---
HTTP_REQUESTS = Counter(
    "uba_http_requests_total", "HTTP requests handled", ["method", "path", "status"]
)
HTTP_DURATION = Histogram(
    "uba_http_request_duration_seconds",
    "Time spent handling a request",
    ["method", "path"],
    # Buckets tuned for a web API (5ms ... 5s), so percentiles are meaningful.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
IN_FLIGHT = Gauge("uba_http_requests_in_flight", "Requests being handled right now")

# --- "is the product working?" (business metrics) ---
BOOKING_EVENTS = Counter("uba_booking_events_total", "Booking lifecycle events", ["event"])
# A live snapshot of bookings by status, refreshed each time Prometheus scrapes.
ACTIVE_BOOKINGS = Gauge("uba_bookings_current", "Bookings right now, by status", ["status"])
FARE_QUOTED = Histogram(
    "uba_fare_quoted_ttd",
    "Fares quoted by the fare model, in TT dollars",
    buckets=(50, 75, 100, 150, 200, 300, 500),
)
SURGE_QUOTES = Counter("uba_fare_surge_quotes_total", "Fare quotes that were in surge")
DEMAND_WAITING = Gauge("uba_demand_waiting_riders", "Riders waiting (pending bookings) at last quote")
DEMAND_FREE = Gauge("uba_demand_free_drivers", "Drivers free at last quote")

# --- "is anyone attacking us?" (security metrics) ---
LOGINS = Counter("uba_logins_total", "Login attempts", ["result"])
PASSWORD_RESETS = Counter("uba_password_resets_total", "Password reset steps", ["step"])


# ---------- logs ----------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        entry.update(getattr(record, "fields", {}))
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # We write our own access log line below, so silence uvicorn's.
    logging.getLogger("uvicorn.access").disabled = True


log = logging.getLogger("uba")


# ---------- wiring it into the app ----------

def setup_observability(app: FastAPI) -> None:
    @app.middleware("http")
    async def observe(request: Request, call_next):
        # Reuse the ID from the proxy if there is one, otherwise make one.
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500
        IN_FLIGHT.inc()
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            IN_FLIGHT.dec()
            duration = time.perf_counter() - started
            # Use the route template ("/api/bookings/{booking_id}"), never the
            # real URL, or every booking would create its own metric series.
            route = request.scope.get("route")
            path = getattr(route, "path", "unmatched")
            if path != "/metrics":
                HTTP_REQUESTS.labels(request.method, path, str(status_code)).inc()
                HTTP_DURATION.labels(request.method, path).observe(duration)

                # The log line carries who, what and how slow, so a single
                # request can be found and understood later. The level rises
                # with trouble: a 500 or a slow call is worth more attention
                # than a routine 200. (The auth dependency sets request.state
                # once a caller is identified; see security.py.)
                fields = {
                    "method": request.method,
                    "path": request.url.path,
                    "route": path,
                    "status": status_code,
                    "duration_ms": round(duration * 1000, 1),
                    "client_ip": request.client.host if request.client else None,
                    "user_id": getattr(request.state, "user_id", None),
                    "role": getattr(request.state, "role", None),
                }
                if status_code >= 500:
                    log.error("request", extra={"fields": fields})
                elif status_code >= 400 or duration > 1.0:
                    log.warning("request", extra={"fields": fields})
                else:
                    log.info("request", extra={"fields": fields})

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        # Not under /api, so the reverse proxy never exposes it to the internet.
        #
        # Some numbers are not events to count but a state to read: "how many
        # bookings are pending right now?". We answer that the moment
        # Prometheus asks, by counting the database here and setting the gauge.
        # (Local imports keep this file free of a circular dependency.)
        from sqlalchemy import func, select

        from app.database import SessionLocal
        from app.models import Booking

        try:
            with SessionLocal() as db:
                counts = dict(db.execute(select(Booking.status, func.count()).group_by(Booking.status)).all())
            for status in ("pending", "accepted", "completed", "cancelled"):
                ACTIVE_BOOKINGS.labels(status).set(counts.get(status, 0))
        except Exception:  # never let a metrics read take the endpoint down
            log.exception("failed to refresh booking gauges")

        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
