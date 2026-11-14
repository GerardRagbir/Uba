from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Destination, User
from app.security import current_user, require_role

router = APIRouter(prefix="/api/destinations", tags=["destinations"])


@router.get("", response_model=list[schemas.DestinationOut])
def list_destinations(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Destination).order_by(Destination.name)).all()


@router.post("", response_model=schemas.DestinationOut, status_code=status.HTTP_201_CREATED)
def add_destination(
    data: schemas.DestinationIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    name = data.name.strip()
    exists = db.scalars(select(Destination).where(func.lower(Destination.name) == name.lower())).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "That destination already exists")
    destination = Destination(name=name, fare=data.fare, latitude=data.latitude, longitude=data.longitude)
    db.add(destination)
    db.commit()
    return destination
