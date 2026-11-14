# storage.py - reads and writes the text files in the data folder
# Each line in a file is one object, with the fields separated by |
# When we move to sqlite3 later, only this file should need to change.

import os

from models import Pax, Driver, Admin, Vehicle, Destination, Booking

# the data folder sits next to this file, so the app works from any folder
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")

USERS_FILE = "users.txt"
VEHICLES_FILE = "vehicles.txt"
DESTINATIONS_FILE = "destinations.txt"
BOOKINGS_FILE = "bookings.txt"


def read_lines(filename):
    path = os.path.join(DATA_FOLDER, filename)
    file = open(path, "a")  # "a" creates the file if it is not there yet
    file.close()

    lines = []
    file = open(path, "r")
    for line in file:
        line = line.strip()
        if line != "":
            lines.append(line)
    file.close()
    return lines


def write_lines(filename, lines):
    path = os.path.join(DATA_FOLDER, filename)
    file = open(path, "w")
    for line in lines:
        file.write(line + "\n")
    file.close()


def save_all(filename, objects):
    # every class has a to_line() method, so this works for all of them
    lines = []
    for item in objects:
        lines.append(item.to_line())
    write_lines(filename, lines)


def load_users():
    users = []
    for line in read_lines(USERS_FILE):
        parts = line.split("|")
        role = parts[0]
        if role == "pax":
            users.append(Pax(parts[1], parts[2], parts[3], parts[4]))
        elif role == "driver":
            users.append(Driver(parts[1], parts[2], parts[3], parts[4]))
        elif role == "admin":
            users.append(Admin(parts[1], parts[2], parts[3]))
    return users


def load_vehicles():
    vehicles = []
    for line in read_lines(VEHICLES_FILE):
        parts = line.split("|")
        vehicles.append(Vehicle(parts[0], parts[1], parts[2], int(parts[3]), parts[4]))
    return vehicles


def load_destinations():
    destinations = []
    for line in read_lines(DESTINATIONS_FILE):
        parts = line.split("|")
        destinations.append(Destination(parts[0], int(parts[1])))
    return destinations


def load_bookings():
    bookings = []
    for line in read_lines(BOOKINGS_FILE):
        parts = line.split("|")
        bookings.append(Booking(int(parts[0]), parts[1], parts[2], parts[3],
                                int(parts[4]), parts[5], parts[6]))
    return bookings
