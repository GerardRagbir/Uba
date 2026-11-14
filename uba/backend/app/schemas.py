"""The shapes of the JSON going in and out of the API (Pydantic models).

FastAPI validates every request against these before our code runs, and uses
them to generate the interactive docs at /api/docs.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Username = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
Password = Field(min_length=8, max_length=128)


# ---------- auth ----------

class RegisterIn(BaseModel):
    role: Literal["pax", "driver"]
    username: str = Username
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Password
    phone: str | None = Field(default=None, max_length=30)
    permit_no: str | None = Field(default=None, max_length=30)


class LoginIn(BaseModel):
    username: str
    password: str


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Password


class Message(BaseModel):
    message: str


# ---------- users ----------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    name: str
    role: str
    phone: str | None = None
    permit_no: str | None = None


class UserCreateIn(BaseModel):
    """Used by an admin to create a driver or another admin."""

    role: Literal["driver", "admin"]
    username: str = Username
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Password
    permit_no: str | None = Field(default=None, max_length=30)


# ---------- destinations ----------

class DestinationIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    fare: int = Field(gt=0, le=10_000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    fare: int
    latitude: float | None = None
    longitude: float | None = None


# ---------- vehicles ----------

class VehicleIn(BaseModel):
    plate: str = Field(min_length=1, max_length=20)
    make: str = Field(max_length=50)
    model: str = Field(max_length=50)
    seats: int = Field(ge=1, le=60)
    driver_id: int


class VehicleUpdateIn(BaseModel):
    plate: str = Field(min_length=1, max_length=20)
    make: str = Field(max_length=50)
    model: str = Field(max_length=50)
    seats: int = Field(ge=1, le=60)


class VehicleOut(BaseModel):
    id: int
    plate: str
    make: str
    model: str
    seats: int
    driver_id: int
    driver_username: str


# ---------- bookings ----------

class BookingIn(BaseModel):
    pickup_id: int
    destination_id: int


class RatingIn(BaseModel):
    rating: Literal["up", "down"]


class FareEstimateOut(BaseModel):
    """The fare model's answer, broken down so a rider can read it line by line."""

    base_fare: int
    final_fare: int
    distance_km: float | None
    time_multiplier: float
    time_label: str
    traffic_multiplier: float
    traffic_label: str
    demand_multiplier: float
    demand_label: str
    surge: bool


class BookingOut(BaseModel):
    id: int
    pickup: str
    pickup_latitude: float | None
    pickup_longitude: float | None
    destination: str
    destination_latitude: float | None
    destination_longitude: float | None
    fare: int
    status: str
    rating: str | None
    pax_username: str
    pax_name: str
    pax_phone: str | None
    driver_username: str | None
    created_at: datetime
