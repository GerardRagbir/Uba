"""The booking lifecycle: pending -> accepted -> completed, or cancelled."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Booking, Destination, User, Vehicle
from app.observability import BOOKING_EVENTS
from app.security import current_user, require_role

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def to_out(booking: Booking) -> schemas.BookingOut:
    return schemas.BookingOut(
        id=booking.id,
        pickup=booking.pickup.name,
        pickup_latitude=booking.pickup.latitude,
        pickup_longitude=booking.pickup.longitude,
        destination=booking.destination.name,
        destination_latitude=booking.destination.latitude,
        destination_longitude=booking.destination.longitude,
        fare=booking.fare,
        status=booking.status,
        rating=booking.rating,
        pax_username=booking.pax.username,
        pax_name=booking.pax.name,
        pax_phone=booking.pax.phone,
        driver_username=booking.driver.username if booking.driver else None,
        created_at=booking.created_at,
    )


def get_booking_or_404(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    return booking


@router.get("", response_model=list[schemas.BookingOut])
def list_bookings(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Each role sees only what it should: the server decides, never the browser."""
    query = select(Booking).order_by(Booking.id.desc())
    if user.role == "pax":
        query = query.where(Booking.pax_id == user.id)
    elif user.role == "driver":
        query = query.where(Booking.driver_id == user.id)
    return [to_out(b) for b in db.scalars(query).all()]


@router.get("/pending", response_model=list[schemas.BookingOut])
def list_pending(db: Session = Depends(get_db), _: User = Depends(require_role("driver"))):
    query = select(Booking).where(Booking.status == "pending").order_by(Booking.id)
    return [to_out(b) for b in db.scalars(query).all()]


@router.post("", response_model=schemas.BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: schemas.BookingIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("pax")),
):
    if data.pickup_id == data.destination_id:
        raise HTTPException(422, "Pickup and destination cannot be the same")
    pickup = db.get(Destination, data.pickup_id)
    destination = db.get(Destination, data.destination_id)
    if pickup is None or destination is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pickup or destination not found")

    # The fare is priced by the fare model, from the route, the time, the
    # traffic and how busy things are right now - never from the request.
    # (See app/fare_model.py.) We recompute here so the charged fare reflects
    # conditions at the moment of booking, not whatever an old quote said.
    from app.routers.fares import quote

    priced = quote(db, pickup, destination)
    booking = Booking(pax_id=user.id, pickup_id=pickup.id, destination_id=destination.id, fare=priced["final_fare"])
    db.add(booking)
    db.commit()
    BOOKING_EVENTS.labels("created").inc()
    return to_out(booking)


@router.post("/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("pax"))):
    booking = get_booking_or_404(db, booking_id)
    if booking.pax_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only pending bookings can be cancelled")
    booking.status = "cancelled"
    db.commit()
    BOOKING_EVENTS.labels("cancelled").inc()
    return to_out(booking)


@router.post("/{booking_id}/accept", response_model=schemas.BookingOut)
def accept_booking(booking_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("driver"))):
    if db.scalars(select(Vehicle).where(Vehicle.driver_id == user.id)).first() is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You need a vehicle before you can accept bookings")
    busy = db.scalars(select(Booking).where(Booking.driver_id == user.id, Booking.status == "accepted")).first()
    if busy:
        raise HTTPException(status.HTTP_409_CONFLICT, "Finish your current job first")

    # Two drivers can press Accept at the same moment. "Read, check, then
    # write" would let both win. Instead we ask the database to do the check
    # and the write as ONE step, and look at how many rows it changed.
    result = db.execute(
        update(Booking)
        .where(Booking.id == booking_id, Booking.status == "pending")
        .values(status="accepted", driver_id=user.id)
    )
    db.commit()
    if result.rowcount == 0:
        get_booking_or_404(db, booking_id)
        raise HTTPException(status.HTTP_409_CONFLICT, "That booking is no longer pending")

    BOOKING_EVENTS.labels("accepted").inc()
    return to_out(get_booking_or_404(db, booking_id))


def get_own_accepted(db: Session, booking_id: int, user: User) -> Booking:
    booking = get_booking_or_404(db, booking_id)
    if booking.driver_id != user.id or booking.status != "accepted":
        raise HTTPException(status.HTTP_409_CONFLICT, "That is not one of your accepted bookings")
    return booking


@router.post("/{booking_id}/complete", response_model=schemas.BookingOut)
def complete_booking(booking_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("driver"))):
    booking = get_own_accepted(db, booking_id, user)
    booking.status = "completed"
    db.commit()
    BOOKING_EVENTS.labels("completed").inc()
    return to_out(booking)


@router.post("/{booking_id}/release", response_model=schemas.BookingOut)
def release_booking(booking_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("driver"))):
    """The driver gives the job up. The passenger still needs a ride, so it goes back to pending."""
    booking = get_own_accepted(db, booking_id, user)
    booking.status = "pending"
    booking.driver_id = None
    db.commit()
    BOOKING_EVENTS.labels("released").inc()
    return to_out(booking)


@router.post("/{booking_id}/rating", response_model=schemas.BookingOut)
def rate_booking(
    booking_id: int,
    data: schemas.RatingIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("pax")),
):
    booking = get_booking_or_404(db, booking_id)
    if booking.pax_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status != "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only completed trips can be rated")
    booking.rating = data.rating
    db.commit()
    BOOKING_EVENTS.labels("rated").inc()
    return to_out(booking)
