"""The fare model: a small, explainable engine that prices a ride.

This is the "AI" in the booking engine. It is deliberately a *transparent*
model, not a black box: it takes a handful of features about a trip and the
world right now, and turns them into a price you can read off line by line.
That matters twice over - a rider should understand why a fare moved, and a
student should be able to see exactly how the decision was made.

The model combines four inputs the system already knows:

  1. route / distance - how far apart pickup and destination are, from the
     map coordinates on each destination (great-circle / haversine distance).
  2. time of day      - a time-based surcharge (late-night rides cost more).
  3. traffic          - rush-hour congestion, inferred from the hour and the
     day of week (weekday mornings and evenings are the worst).
  4. demand           - how many riders are waiting versus how many drivers
     are free right now; scarce drivers push the price up ("surge").

    final_fare = base_fare x time x traffic x demand      (then rounded)

`base_fare` is the destination's flat fare, which already reflects the usual
route, so the multipliers only express how *today* differs from normal.

How this becomes "real" machine learning later
-----------------------------------------------
Each `*_factor` function below is a hand-set rule. In a production system you
would instead TRAIN a model on historical trips (features in, the price riders
actually accepted out) and let it learn these weights. The shape here - turn
raw inputs into numeric features, combine them into one output - is exactly
the shape of that regression; only the source of the numbers changes. The
feature breakdown this returns is also what you would log to train on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

# --- knobs, gathered in one place so they are easy to see and to tune ---

NIGHT_HOURS = range(22, 24)         # 10pm-midnight
EARLY_HOURS = range(0, 5)           # midnight-5am
WEEKDAY_RUSH = (range(6, 9), range(15, 18))  # morning and evening peaks
MAX_TIME_MULTIPLIER = 1.25
MAX_TRAFFIC_MULTIPLIER = 1.40
MAX_DEMAND_MULTIPLIER = 2.00        # the surge cap: a fare never more than doubles
SURGE_STARTS_AT = 1.25             # demand multiplier above this counts as "surge"


@dataclass
class Factor:
    """One multiplier plus a short human-readable reason."""

    value: float
    label: str


# ---------- feature 1: route / distance ----------

def distance_km(
    lat1: float | None, lng1: float | None, lat2: float | None, lng2: float | None
) -> float | None:
    """Great-circle distance between two points, in kilometres (haversine).

    Returns None if either point has no coordinates, so the caller can simply
    leave distance out rather than guess.
    """
    if None in (lat1, lng1, lat2, lng2):
        return None
    radius = 6371.0  # earth radius in km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(radius * 2 * math.asin(math.sqrt(a)), 1)


# ---------- feature 2: time of day ----------

def time_factor(when: datetime) -> Factor:
    hour = when.hour
    if hour in EARLY_HOURS:
        return Factor(MAX_TIME_MULTIPLIER, "late-night surcharge")
    if hour in NIGHT_HOURS:
        return Factor(1.15, "evening surcharge")
    return Factor(1.0, "standard daytime rate")


# ---------- feature 3: traffic ----------

def traffic_factor(when: datetime) -> Factor:
    # Monday is 0, Sunday is 6. Rush hour only bites on weekdays.
    weekday = when.weekday()
    hour = when.hour
    if weekday < 5 and any(hour in window for window in WEEKDAY_RUSH):
        return Factor(MAX_TRAFFIC_MULTIPLIER, "rush-hour traffic")
    if weekday >= 5 and 11 <= hour <= 19:
        return Factor(1.15, "weekend traffic")
    return Factor(1.0, "light traffic")


# ---------- feature 4: demand ----------

def demand_factor(waiting_riders: int, free_drivers: int) -> Factor:
    """More waiting riders than free drivers pushes the price up (surge)."""
    if free_drivers <= 0:
        # No one free at all: apply the full cap, but never beyond it.
        level = MAX_DEMAND_MULTIPLIER if waiting_riders > 0 else 1.0
        return Factor(level, "no drivers free" if waiting_riders else "standard demand")

    ratio = waiting_riders / free_drivers
    # Each waiting rider per free driver adds 40%, capped so fares never run away.
    multiplier = min(1.0 + 0.4 * ratio, MAX_DEMAND_MULTIPLIER)
    multiplier = round(multiplier, 2)
    if multiplier >= SURGE_STARTS_AT:
        return Factor(multiplier, f"high demand ({waiting_riders} waiting, {free_drivers} free)")
    return Factor(multiplier, "standard demand")


# ---------- the model ----------

def estimate_fare(
    base_fare: int,
    pickup: tuple[float | None, float | None],
    destination: tuple[float | None, float | None],
    waiting_riders: int,
    free_drivers: int,
    when: datetime | None = None,
) -> dict:
    """Price a trip and return the full breakdown, not just the number."""
    when = when or datetime.now(timezone.utc)

    time = time_factor(when)
    traffic = traffic_factor(when)
    demand = demand_factor(waiting_riders, free_drivers)
    km = distance_km(pickup[0], pickup[1], destination[0], destination[1])

    final = round(base_fare * time.value * traffic.value * demand.value)

    return {
        "base_fare": base_fare,
        "final_fare": final,
        "distance_km": km,
        "time_multiplier": time.value,
        "time_label": time.label,
        "traffic_multiplier": traffic.value,
        "traffic_label": traffic.label,
        "demand_multiplier": demand.value,
        "demand_label": demand.label,
        "surge": demand.value >= SURGE_STARTS_AT,
    }
