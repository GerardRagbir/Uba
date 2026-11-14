"""Register, log in, log out, and the forgot-password flow."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import schemas
from app.config import get_settings
from app.database import get_db
from app.emailer import send_password_reset
from app.models import Driver, PasswordResetToken, Pax, User
from app.observability import LOGINS, PASSWORD_RESETS
from app.security import (
    create_access_token,
    current_user,
    hash_password,
    hash_reset_token,
    new_reset_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def username_or_email_taken(db: Session, username: str, email: str) -> bool:
    query = select(User).where(or_(User.username == username, User.email == email))
    return db.scalars(query).first() is not None


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    """Anyone may register as a passenger or a driver. Admins are created by admins."""
    if username_or_email_taken(db, data.username, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "That username or email is already in use")

    common = dict(
        username=data.username,
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
    )
    if data.role == "driver":
        user = Driver(**common, permit_no=data.permit_no)
    else:
        user = Pax(**common, phone=data.phone)
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=schemas.UserOut)
def login(data: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalars(select(User).where(User.username == data.username)).first()
    if user is None or not verify_password(data.password, user.password_hash):
        LOGINS.labels("failed").inc()
        # Same answer for "no such user" and "wrong password", on purpose.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")

    LOGINS.labels("ok").inc()
    response.set_cookie(
        settings.cookie_name,
        create_access_token(user),
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,   # JavaScript cannot read it
        samesite="lax",  # not sent on cross-site POSTs, which blocks most CSRF
        secure=settings.cookie_secure,
        path="/",
    )
    return user


@router.post("/logout", response_model=schemas.Message)
def logout(response: Response):
    response.delete_cookie(settings.cookie_name, path="/")
    return {"message": "Logged out"}


@router.get("/me", response_model=schemas.UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/forgot-password", response_model=schemas.Message, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    data: schemas.ForgotPasswordIn, background: BackgroundTasks, db: Session = Depends(get_db)
):
    PASSWORD_RESETS.labels("requested").inc()
    user = db.scalars(select(User).where(User.email == data.email)).first()
    if user is not None:
        token, token_hash = new_reset_token()
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.reset_token_minutes)
        db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires))
        db.commit()
        # Sent after the response, so the request is fast either way.
        background.add_task(send_password_reset, user.email, user.name, token)

    # The answer is identical whether or not the email exists, so this
    # endpoint cannot be used to find out who has an account.
    return {"message": "If that email has an account, a reset link is on its way."}


@router.post("/reset-password", response_model=schemas.Message)
def reset_password(data: schemas.ResetPasswordIn, db: Session = Depends(get_db)):
    record = db.scalars(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_reset_token(data.token))
    ).first()

    now = datetime.now(timezone.utc)
    expired = True
    if record is not None:
        expires_at = record.expires_at
        if expires_at.tzinfo is None:  # SQLite drops the timezone
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        expired = expires_at < now
    if record is None or record.used_at is not None or expired:
        PASSWORD_RESETS.labels("rejected").inc()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That reset link is invalid or has expired")

    user = db.get(User, record.user_id)
    user.password_hash = hash_password(data.new_password)
    record.used_at = now  # a link works once
    db.commit()
    PASSWORD_RESETS.labels("completed").inc()
    return {"message": "Password changed. You can now log in."}
