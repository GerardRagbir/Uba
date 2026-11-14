"""The FastAPI application: creates the app and plugs everything together."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, SessionLocal, engine, get_db
from app.observability import log, setup_logging, setup_observability
from app.routers import auth, bookings, destinations, fares, users, vehicles
from app.seed import seed

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts."""
    setup_logging()
    # Fine for a demo. A real project uses migrations (Alembic) instead, so
    # that the tables can change without losing the data already in them.
    Base.metadata.create_all(engine)
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed(db)
    if settings.jwt_secret == "change-me-in-production-with-a-long-random-value" and settings.environment == "production":
        raise RuntimeError("UBA_JWT_SECRET must be set in production")
    log.info("api started", extra={"fields": {"environment": settings.environment}})
    yield


app = FastAPI(
    title="UBA Taxi Booking API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
setup_observability(app)

for router in (auth.router, destinations.router, bookings.router, fares.router, vehicles.router, users.router):
    app.include_router(router)


@app.get("/api/health", tags=["ops"])
def health():
    """Liveness: is the process running? Used by Docker's healthcheck."""
    return {"status": "ok"}


@app.get("/api/ready", tags=["ops"])
def ready(db: Session = Depends(get_db)):
    """Readiness: can we actually serve requests, i.e. is the database reachable?"""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database is not reachable")
    return {"status": "ready"}
