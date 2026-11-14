# ============================================================
# STOP 5 of 10 - session.py - the data, and who is logged in
# You came from: database.py      Next stop: gui/base_page.py
# ============================================================
# The Session still hands every page the same four lists of objects, and
# the same find_... methods. What changed is where the lists come from and
# how a change is saved:
#
#   uba-gui        change the list, then write the WHOLE file again
#   uba-advanced   tell the database about the ONE thing that changed
#
# NOTICE: there is no SQL in this file and no NiceGUI either. The Session
# sits in the middle: pages on one side, database.py on the other.

import database


class Session:
    def __init__(self):
        # None means nobody is logged in yet. The login page sets this.
        self.current_user = None
        self.reload()

    def reload(self):
        # reads everything from the database again.
        # NOTICE: BasePage.show() calls this every time a page is drawn, so
        # the screen always shows what is in the database right now. If a
        # driver accepts a booking in another browser window, the passenger
        # sees it the next time their page is redrawn. In uba-gui they had
        # to log out and back in.
        self.users = database.load_users()
        self.vehicles = database.load_vehicles()
        self.destinations = database.load_destinations()
        self.bookings = database.load_bookings()

        # the lists now hold brand new objects, so point current_user at
        # the new object for the same person
        if self.current_user is not None:
            self.current_user = self.find_user(self.current_user.username)

    # ---------- finding one object in a list ----------
    # Each of these returns the object, or None when there is no match.
    # The pages always check for None before using the answer.

    def find_user(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def find_destination(self, name):
        for destination in self.destinations:
            if destination.name == name:
                return destination
        return None

    def find_vehicle_for_driver(self, username):
        for vehicle in self.vehicles:
            if vehicle.driver_username == username:
                return vehicle
        return None

    # ---------- adding something new ----------
    # save it in the database AND put it in our list

    def add_user(self, user):
        database.add_user(user)
        self.users.append(user)

    def add_vehicle(self, vehicle):
        database.add_vehicle(vehicle)
        self.vehicles.append(vehicle)

    def add_destination(self, destination):
        database.add_destination(destination)
        self.destinations.append(destination)

    def add_booking(self, booking):
        # the database chooses the booking number and hands it back to us
        booking.booking_id = database.add_booking(booking)
        self.bookings.append(booking)

    # ---------- changing something that already exists ----------
    # the page changes the object's attributes first, then calls one of
    # these to save that one object

    def update_user(self, user):
        database.update_user(user)

    def update_vehicle(self, vehicle):
        database.update_vehicle(vehicle)

    def update_booking(self, booking):
        database.update_booking(booking)
