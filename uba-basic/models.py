# models.py - the classes (objects) used in the UBA taxi booking app


class User:
    """Base class. Pax, Driver and Admin all inherit from this."""

    def __init__(self, username, password, name):
        self.username = username
        self.password = password
        self.name = name
        self.role = "user"

    def check_password(self, password):
        return self.password == password

    def to_line(self):
        # one line of text for the users file
        return self.role + "|" + self.username + "|" + self.password + "|" + self.name

    def show(self):
        print(self.role.upper() + " - " + self.name + " (" + self.username + ")")


class Pax(User):
    """A passenger. Has a phone number so the driver can call."""

    def __init__(self, username, password, name, phone):
        super().__init__(username, password, name)
        self.role = "pax"
        self.phone = phone

    def to_line(self):
        return super().to_line() + "|" + self.phone

    def show(self):
        super().show()
        print("   Phone: " + self.phone)


class Driver(User):
    """A driver. Has a driver's permit number."""

    def __init__(self, username, password, name, permit_no):
        super().__init__(username, password, name)
        self.role = "driver"
        self.permit_no = permit_no

    def to_line(self):
        return super().to_line() + "|" + self.permit_no

    def show(self):
        super().show()
        print("   Permit: " + self.permit_no)


class Admin(User):
    """An admin. Nothing extra to store, but gets the admin menu."""

    def __init__(self, username, password, name):
        super().__init__(username, password, name)
        self.role = "admin"


class Vehicle:
    def __init__(self, plate, make, model, seats, driver_username):
        self.plate = plate
        self.make = make
        self.model = model
        self.seats = seats
        self.driver_username = driver_username

    def to_line(self):
        return (self.plate + "|" + self.make + "|" + self.model + "|"
                + str(self.seats) + "|" + self.driver_username)

    def show(self):
        print(self.plate + " - " + self.make + " " + self.model
              + ", " + str(self.seats) + " seats, driver: " + self.driver_username)


class Destination:
    def __init__(self, name, fare):
        self.name = name
        self.fare = fare  # flat fare in TT dollars

    def to_line(self):
        return self.name + "|" + str(self.fare)

    def show(self):
        print(self.name + " - TT$" + str(self.fare))


class Booking:
    def __init__(self, booking_id, pax_username, pickup, destination, fare, status, driver_username):
        self.booking_id = booking_id
        self.pax_username = pax_username
        self.pickup = pickup
        self.destination = destination
        self.fare = fare
        self.status = status  # pending, accepted, completed or cancelled
        self.driver_username = driver_username  # "none" until a driver accepts

    def to_line(self):
        return (str(self.booking_id) + "|" + self.pax_username + "|" + self.pickup + "|"
                + self.destination + "|" + str(self.fare) + "|" + self.status + "|"
                + self.driver_username)

    def show(self):
        print("Booking #" + str(self.booking_id) + ": " + self.pickup + " -> " + self.destination
              + ", TT$" + str(self.fare) + ", " + self.status
              + ", pax: " + self.pax_username + ", driver: " + self.driver_username)
