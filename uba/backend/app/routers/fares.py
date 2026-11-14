"""The fare estimate endpoint - the model exposed over the API.

The frontend calls this as a rider picks their pickup and destination, so the
price (and why it is what it is) updates live before they book.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.fare_model import estimate_fare
from app.models import Booking, Destination, User, Vehicle
from app.observability import DEMAND_FREE, DEMAND_WAITING, FARE_QUOTED, SURGE_QUOTES
from app.security import current_user

router = APIRouter(prefix="/api/fare", tags=["fare"])


def market_conditions(db: Session) -> tuple[int, int]:
    """How busy things are right now: (riders waiting, drivers free)."""
    waiting_riders = db.scalar(select(func.count()).where(Booking.status == "pending")) or 0

    # A driver is "free" if they have a vehicle and are not mid-job.
    drivers_with_vehicles = db.scalar(select(func.count()).select_from(Vehicle)) or 0
    busy_drivers = db.scalar(
        select(func.count(func.distinct(Booking.driver_id))).where(Booking.status == "accepted")
    ) or 0
    free_drivers = max(drivers_with_vehicles - busy_drivers, 0)
    return waiting_riders, free_drivers


def quote(db: Session, pickup: Destination, destination: Destination) -> dict:
    waiting_riders, free_drivers = market_conditions(db)
    priced = estimate_fare(
        base_fare=destination.fare,
        pickup=(pickup.latitude, pickup.longitude),
        destination=(destination.latitude, destination.longitude),
        waiting_riders=waiting_riders,
        free_drivers=free_drivers,
    )
    # Feed the observability stack: every quote tells us the going price and
    # how tight supply and demand are right now.
    FARE_QUOTED.observe(priced["final_fare"])
    DEMAND_WAITING.set(waiting_riders)
    DEMAND_FREE.set(free_drivers)
    if priced["surge"]:
        SURGE_QUOTES.inc()
    return priced


@router.get("/estimate", response_model=schemas.FareEstimateOut)
def estimate(
    pickup_id: int,
    destination_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    if pickup_id == destination_id:
        raise HTTPException(422, "Pickup and destination cannot be the same")
    pickup = db.get(Destination, pickup_id)
    destination = db.get(Destination, destination_id)
    if pickup is None or destination is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pickup or destination not found")
    return quote(db, pickup, destination)
