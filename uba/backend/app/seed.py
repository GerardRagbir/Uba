"""Demo data, added once to an empty database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Admin, Destination, Driver, Pax, User, Vehicle
from app.observability import log
from app.security import hash_password

# (name, fare in TT dollars, latitude, longitude)
DESTINATIONS = [
    ("Port of Spain", 60, 10.6549, -61.5019),
    ("San Fernando", 120, 10.2796, -61.4589),
    ("Chaguanas", 80, 10.5167, -61.4111),
    ("Arima", 90, 10.6372, -61.2823),
    ("Piarco Airport", 100, 10.5954, -61.3372),
    ("Maracas Bay", 150, 10.7585, -61.4337),
    ("Tunapuna", 70, 10.6525, -61.3888),
    ("Couva", 100, 10.4225, -61.4500),
    ("Sangre Grande", 140, 10.5871, -61.1301),
    ("Point Fortin", 200, 10.1741, -61.6841),
]


def seed(db: Session) -> None:
    if db.scalars(select(User)).first() is not None:
        return

    # Every demo account uses the same password, so they are easy to remember.
    password_hash = hash_password("password123")

    driver = Driver(username="driver", email="driver@example.com", name="Demo Driver",
                    password_hash=password_hash, permit_no="DP445821")
    driver2 = Driver(username="driver2", email="driver2@example.com", name="Demo Driver Two",
                     password_hash=password_hash, permit_no="DP390177")
    db.add_all([
        Admin(username="admin", email="admin@example.com", name="Demo Admin", password_hash=password_hash),
        driver,
        driver2,
        Pax(username="pax", email="pax@example.com", name="Demo Passenger",
            password_hash=password_hash, phone="868-555-0142"),
    ])
    db.flush()  # gives the drivers their ids
    db.add_all([
        Vehicle(plate="HDK 2210", make="Toyota", model="Axio", seats=4, driver_id=driver.id),
        Vehicle(plate="HCZ 7734", make="Nissan", model="Tiida", seats=4, driver_id=driver2.id),
    ])
    db.add_all([
        Destination(name=name, fare=fare, latitude=latitude, longitude=longitude)
        for name, fare, latitude, longitude in DESTINATIONS
    ])
    db.commit()
    log.info("demo data added")
