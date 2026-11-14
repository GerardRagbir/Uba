"""Password hashing, login tokens, and the "who is calling?" dependencies."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User

settings = get_settings()
hasher = PasswordHasher()  # Argon2id, the current recommended password hash


# ---------- passwords ----------

def hash_password(password: str) -> str:
    # The salt is generated for us and stored inside the returned string.
    return hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except (Argon2Error, InvalidHashError):
        return False


# ---------- login tokens (JWT) ----------

def create_access_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user.id), "role": user.role, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency: returns the logged-in user, or answers 401.

    The token travels in an httpOnly cookie, so JavaScript in the browser can
    never read it. That removes the most common way tokens are stolen (XSS).
    """
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    # Record who this is on the request, so the access log can name them.
    request.state.user_id = user.id
    request.state.role = user.role
    return user


def require_role(*roles: str):
    """Dependency factory: `Depends(require_role("admin"))` protects a route."""

    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this")
        return user

    return checker


# ---------- password-reset tokens ----------

def new_reset_token() -> tuple[str, str]:
    """Returns (token to email to the user, hash to store in the database)."""
    token = secrets.token_urlsafe(32)
    return token, hash_reset_token(token)


def hash_reset_token(token: str) -> str:
    # The token is already long and random, so a fast hash is enough here.
    return hashlib.sha256(token.encode()).hexdigest()
