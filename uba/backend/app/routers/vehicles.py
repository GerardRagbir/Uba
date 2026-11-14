from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Driver, User, Vehicle
from app.security import require_role

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


def to_out(vehicle: Vehicle) -> schemas.VehicleOut:
    return schemas.VehicleOut(
        id=vehicle.id,
        plate=vehicle.plate,
        make=vehicle.make,
        model=vehicle.model,
        seats=vehicle.seats,
        driver_id=vehicle.driver_id,
        driver_username=vehicle.driver.username,
    )


def plate_taken(db: Session, plate: str, ignore_id: int | None = None) -> bool:
    other = db.scalars(select(Vehicle).where(Vehicle.plate == plate)).first()
    return other is not None and other.id != ignore_id


@router.get("", response_model=list[schemas.VehicleOut])
def list_vehicles(db: Session = Depends(get_db), _: User = Depends(require_role("admin"))):
    return [to_out(v) for v in db.scalars(select(Vehicle).order_by(Vehicle.plate)).all()]


@router.post("", response_model=schemas.VehicleOut, status_code=status.HTTP_201_CREATED)
def add_vehicle(data: schemas.VehicleIn, db: Session = Depends(get_db), _: User = Depends(require_role("admin"))):
    plate = data.plate.strip().upper()
    driver = db.get(Driver, data.driver_id)
    if driver is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver not found")
    if driver.vehicle is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "That driver already has a vehicle")
    if plate_taken(db, plate):
        raise HTTPException(status.HTTP_409_CONFLICT, "That plate is already registered")
    vehicle = Vehicle(plate=plate, make=data.make, model=data.model, seats=data.seats, driver_id=driver.id)
    db.add(vehicle)
    db.commit()
    return to_out(vehicle)


@router.get("/mine", response_model=schemas.VehicleOut | None)
def my_vehicle(db: Session = Depends(get_db), user: User = Depends(require_role("driver"))):
    vehicle = db.scalars(select(Vehicle).where(Vehicle.driver_id == user.id)).first()
    return to_out(vehicle) if vehicle else None


@router.put("/mine", response_model=schemas.VehicleOut)
def update_my_vehicle(
    data: schemas.VehicleUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("driver")),
):
    vehicle = db.scalars(select(Vehicle).where(Vehicle.driver_id == user.id)).first()
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No vehicle assigned yet")
    plate = data.plate.strip().upper()
    if plate_taken(db, plate, ignore_id=vehicle.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "That plate is already registered")
    vehicle.plate, vehicle.make, vehicle.model, vehicle.seats = plate, data.make, data.model, data.seats
    db.commit()
    return to_out(vehicle)
