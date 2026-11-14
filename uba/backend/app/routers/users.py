from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Admin, Driver, User
from app.routers.auth import username_or_email_taken
from app.security import hash_password, require_role

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_role("admin"))):
    return db.scalars(select(User).order_by(User.username)).all()


@router.post("", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: schemas.UserCreateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """Only an admin can create another admin."""
    if username_or_email_taken(db, data.username, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "That username or email is already in use")
    common = dict(
        username=data.username,
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
    )
    user = Admin(**common) if data.role == "admin" else Driver(**common, permit_no=data.permit_no)
    db.add(user)
    db.commit()
    return user
