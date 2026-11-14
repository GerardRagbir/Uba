# ============================================================
# STOP 3 of 10 - models.py - the classes (objects) used in the app
# You came from: security.py      Next stop: database.py
# ============================================================
# The same classes and the same inheritance as before: Pax, Driver and
# Admin inherit from User. Three things have changed since uba-gui:
#
#   1. to_line() and show() are gone. They existed to write text files and
#      to print to the console, and this version does neither.
#   2. User no longer holds a password. It holds a password HASH, a salt,
#      and a security question with the hash of its answer.
#   3. Booking has a rating attribute. In uba-gui the ratings sat in their
#      own file because we were not allowed to change this class.

import security


class User:
    """Base class. Pax, Driver and Admin all inherit from this."""

    def __init__(self, username, name):
        self.username = username
        self.name = name
        self.role = "user"

        # NOTICE: a brand new user gets a fresh salt and empty hashes. The
        # password and the security answer are set afterwards with the
        # methods below. When a user is loaded from the database, these
        # four values are replaced with the saved ones (see database.py).
        self.salt = security.new_salt()
        self.password_hash = ""
        self.question = ""
        self.answer_hash = ""

    # ---------- password ----------

    def set_password(self, password):
        # NOTICE: the password itself is not kept anywhere, only its hash
        self.password_hash = security.hash_text(password, self.salt)

    def check_password(self, password):
        # scramble what was typed the same way, then compare the scrambles
        return security.hash_text(password, self.salt) == self.password_hash

    # ---------- security question (used by "Forgot password") ----------

    def set_security_answer(self, question, answer):
        # the answer is as secret as a password, so it is hashed as well.
        # strip() and lower() mean " Arima" and "arima" count as the same.
        self.question = question
        self.answer_hash = security.hash_text(answer.strip().lower(), self.salt)

    def check_answer(self, answer):
        if self.answer_hash == "":
            return False   # this user never set a security answer
        return security.hash_text(answer.strip().lower(), self.salt) == self.answer_hash


class Pax(User):
    """A passenger. Has a phone number so the driver can call."""

    def __init__(self, username, name, phone):
        super().__init__(username, name)
        self.role = "pax"
        self.phone = phone


class Driver(User):
    """A driver. Has a driver's permit number."""

    def __init__(self, username, name, permit_no):
        super().__init__(username, name)
        self.role = "driver"
        self.permit_no = permit_no


class Admin(User):
    """An admin. Nothing extra to store, but gets the admin page."""

    def __init__(self, username, name):
        super().__init__(username, name)
        self.role = "admin"

# NOTICE: set_password, check_password, set_security_answer and check_answer
# are written once in User. Pax, Driver and Admin all inherit them, so
# "Forgot password" works for every kind of account with no extra code.


class Vehicle:
    def __init__(self, plate, make, model, seats, driver_username):
        self.plate = plate
        self.make = make
        self.model = model
        self.seats = seats
        self.driver_username = driver_username


class Destination:
    def __init__(self, name, fare):
        self.name = name
        self.fare = fare  # flat fare in TT dollars


class Booking:
    def __init__(self, booking_id, pax_username, pickup, destination, fare, status, driver_username, rating):
        self.booking_id = booking_id  # given by the database, 0 until it is saved
        self.pax_username = pax_username
        self.pickup = pickup
        self.destination = destination
        self.fare = fare
        self.status = status  # pending, accepted, completed or cancelled
        self.driver_username = driver_username  # "none" until a driver accepts
        self.rating = rating  # "none", "up" or "down"
