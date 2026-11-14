"""Database tables, written as Python classes (SQLAlchemy ORM).

The inheritance from the earlier versions is still here: Pax, Driver and Admin
inherit from User. SQLAlchemy stores all of them in ONE table and uses the
`role` column to decide which class to build for each row. This is called
single-table inheritance.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    # Only one of these is filled in, depending on the role.
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    permit_no: Mapped[str | None] = mapped_column(String(30), nullable=True)

    __mapper_args__ = {"polymorphic_on": "role", "polymorphic_identity": "user"}


class Pax(User):
    __mapper_args__ = {"polymorphic_identity": "pax"}


class Driver(User):
    __mapper_args__ = {"polymorphic_identity": "driver"}

    vehicle: Mapped["Vehicle | None"] = relationship(back_populates="driver", uselist=False)


class Admin(User):
    __mapper_args__ = {"polymorphic_identity": "admin"}


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(20), unique=True)
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    seats: Mapped[int] = mapped_column(Integer)
    # unique=True: the database itself guarantees one vehicle per driver.
    driver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    driver: Mapped[Driver] = relationship(back_populates="vehicle")


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    fare: Mapped[int] = mapped_column(Integer)  # flat fare in TT dollars
    # Where it is on the map. Optional: a destination without coordinates
    # still works, the map simply does not move to it.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    pax_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    pickup_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    fare: Mapped[int] = mapped_column(Integer)  # copied at booking time, so later price changes do not rewrite history
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    rating: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "up" or "down"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    pax: Mapped[User] = relationship(foreign_keys=[pax_id])
    driver: Mapped[User | None] = relationship(foreign_keys=[driver_id])
    pickup: Mapped[Destination] = relationship(foreign_keys=[pickup_id])
    destination: Mapped[Destination] = relationship(foreign_keys=[destination_id])


class PasswordResetToken(Base):
    """A one-time, short-lived token emailed to a user who forgot their password.

    Only a hash of the token is stored, for the same reason we only store a
    hash of a password: a leaked database must not let anyone reset accounts.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
