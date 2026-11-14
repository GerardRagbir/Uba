# ============================================================
# STOP 2 of 7 - session.py - the data, and who is logged in
# You came from: main.py          Next stop: gui/base_page.py
# ============================================================
# NOTICE: in the console version the lists (users, vehicles, destinations,
# bookings) and the find_... functions sat loose at the top of main.py.
# Here the same lists and the same functions are gathered into one class,
# so that one Session object can be handed to every page.
#
# NOTICE: there is no NiceGUI in this file. It is plain Python that you
# have already written once. It uses storage.py, which we did not change.

import storage

# storage.py does not know about this file, but its read_lines and
# write_lines functions work with any file name in the data folder
RATINGS_FILE = "ratings.txt"


class Session:
    def __init__(self):
        # loaded from the same text files the console app uses
        self.users = storage.load_users()
        self.vehicles = storage.load_vehicles()
        self.destinations = storage.load_destinations()
        self.bookings = storage.load_bookings()

        # NOTICE: ratings are new in the GUI version. models.py has no place
        # for a rating and we promised not to change it, so the ratings get
        # their own small file and their own dict:
        #     {booking number: "up" or "down"}     for example {3: "up"}
        # A dict suits this because we always look a rating up BY its
        # booking number. A booking with no entry has not been rated yet.
        self.ratings = {}
        for line in storage.read_lines(RATINGS_FILE):
            parts = line.split("|")
            self.ratings[int(parts[0])] = parts[1]

        # None means nobody is logged in yet. The login page sets this.
        self.current_user = None

    # ---------- finding one object in a list ----------
    # Each of these returns the object, or None when there is no match.
    # The pages always check for None before using the answer.

    def find_user(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def find_booking(self, booking_id):
        for booking in self.bookings:
            if booking.booking_id == booking_id:
                return booking
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

    def rating_text(self, booking_id):
        # the words (or picture) to show for a booking's rating
        if booking_id in self.ratings:
            if self.ratings[booking_id] == "up":
                return "👍"
            return "👎"
        return "Not rated"

    # ---------- saving a list back to its text file ----------
    # A page calls one of these straight after it changes a list.
    # When we move to sqlite3, the pages will not need to change at all.

    def save_users(self):
        storage.save_all(storage.USERS_FILE, self.users)

    def save_vehicles(self):
        storage.save_all(storage.VEHICLES_FILE, self.vehicles)

    def save_destinations(self):
        storage.save_all(storage.DESTINATIONS_FILE, self.destinations)

    def save_bookings(self):
        storage.save_all(storage.BOOKINGS_FILE, self.bookings)

    def save_ratings(self):
        # one line per rating, in the same style as the other files: 3|up
        lines = []
        for booking_id in self.ratings:
            lines.append(str(booking_id) + "|" + self.ratings[booking_id])
        storage.write_lines(RATINGS_FILE, lines)
