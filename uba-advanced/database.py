# ============================================================
# STOP 4 of 10 - database.py - reads and writes the sqlite3 database
# You came from: models.py        Next stop: gui/session.py
# ============================================================
# This file replaces storage.py. Everything is now kept in ONE file,
# data/uba.db, which holds four tables. A table is like a spreadsheet:
# columns with names, and one row for each object.
#
# We talk to the database in a language called SQL. You only need four
# kinds of sentence, and all four are in this file:
#     CREATE TABLE ...          make a table (once)
#     INSERT INTO ... VALUES    add a row
#     SELECT ... FROM           read rows
#     UPDATE ... SET ... WHERE  change the rows that match
#
# NOTICE: compare with the text files. Before, changing one booking meant
# writing the whole bookings file again. Now we change that one row.
#
# NOTICE: this is the ONLY file that contains SQL. The pages never see it.
# They call the functions below and get ordinary Python objects back.

import os
import sqlite3

from models import Pax, Driver, Admin, Vehicle, Destination, Booking

# the data folder sits next to this file, so the app works from any folder
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")
DB_FILE = os.path.join(DATA_FOLDER, "uba.db")


# ---------- two helpers that every other function uses ----------

def run(sql, values=()):
    # for SQL that CHANGES the database (CREATE, INSERT, UPDATE).
    # Returns the id the database gave to a newly inserted row.
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.execute(sql, values)
    connection.commit()   # commit = really save the change
    new_id = cursor.lastrowid
    connection.close()
    return new_id


def fetch(sql, values=()):
    # for SQL that READS the database (SELECT).
    # Returns a list of tuples, one tuple for each row that was found.
    connection = sqlite3.connect(DB_FILE)
    rows = connection.execute(sql, values).fetchall()
    connection.close()
    return rows

# NOTICE: the question marks. We never build SQL by gluing the user's text
# into the sentence with +. We write ? where a value goes and hand the
# values over separately, in a tuple. The database then treats them purely
# as data. Gluing text in would let someone type SQL into the username box
# and have the database run it. That attack is called SQL injection.


# ---------- making the tables ----------

def setup():
    # called once, when the app starts (see main.py)
    if not os.path.exists(DATA_FOLDER):
        os.mkdir(DATA_FOLDER)

    # IF NOT EXISTS means this does nothing when the table is already there

    # NOTICE: one table holds all three kinds of user. A row uses the phone
    # column if it is a pax and the permit_no column if it is a driver, and
    # leaves the other one empty. PRIMARY KEY means no two rows may have
    # the same username: the database itself now refuses duplicates.
    run("""CREATE TABLE IF NOT EXISTS users (
               username      TEXT PRIMARY KEY,
               role          TEXT,
               name          TEXT,
               phone         TEXT,
               permit_no     TEXT,
               password_hash TEXT,
               salt          TEXT,
               question      TEXT,
               answer_hash   TEXT)""")

    run("""CREATE TABLE IF NOT EXISTS vehicles (
               plate           TEXT PRIMARY KEY,
               make            TEXT,
               model           TEXT,
               seats           INTEGER,
               driver_username TEXT)""")

    run("""CREATE TABLE IF NOT EXISTS destinations (
               name TEXT PRIMARY KEY,
               fare INTEGER)""")

    # AUTOINCREMENT: the database hands out the booking numbers 1, 2, 3...
    # by itself and never uses the same number twice.
    run("""CREATE TABLE IF NOT EXISTS bookings (
               booking_id      INTEGER PRIMARY KEY AUTOINCREMENT,
               pax_username    TEXT,
               pickup          TEXT,
               destination     TEXT,
               fare            INTEGER,
               status          TEXT,
               driver_username TEXT,
               rating          TEXT)""")

    # a brand new database has no users, so give it something to start with
    if len(fetch("SELECT username FROM users")) == 0:
        add_starter_data()


def add_starter_data():
    # every starter account has the same security question and answer
    question = "What town were you born in?"
    answer = "arima"

    admin = Admin("admin", "Site Admin")
    admin.set_password("admin123")

    kwame = Driver("kwame", "Kwame Joseph", "DP445821")
    kwame.set_password("drive123")

    shiva = Driver("shiva", "Shiva Maharaj", "DP390177")
    shiva.set_password("drive123")

    gerard = Pax("gerard", "Gerard Ragbir", "868-555-0142")
    gerard.set_password("pax123")

    for user in [admin, kwame, shiva, gerard]:
        user.set_security_answer(question, answer)
        add_user(user)

    add_vehicle(Vehicle("HDK 2210", "Toyota", "Axio", 4, "kwame"))
    add_vehicle(Vehicle("HCZ 7734", "Nissan", "Tiida", 4, "shiva"))

    # a list of tuples: (name, fare in TT dollars)
    starter_destinations = [
        ("Port of Spain", 60), ("San Fernando", 120), ("Chaguanas", 80),
        ("Arima", 90), ("Piarco Airport", 100), ("Maracas Bay", 150),
        ("Tunapuna", 70), ("Couva", 100), ("Sangre Grande", 140),
        ("Point Fortin", 200),
    ]
    for name, fare in starter_destinations:
        add_destination(Destination(name, fare))


# ---------- users ----------

def load_users():
    users = []
    rows = fetch("""SELECT username, role, name, phone, permit_no,
                           password_hash, salt, question, answer_hash
                    FROM users""")
    for row in rows:
        # each row is a tuple, in the same order as the SELECT above
        username, role, name, phone, permit_no, password_hash, salt, question, answer_hash = row

        # the role column decides which class to make
        if role == "pax":
            user = Pax(username, name, phone)
        elif role == "driver":
            user = Driver(username, name, permit_no)
        else:
            user = Admin(username, name)

        # replace the fresh values from __init__ with the saved ones
        user.password_hash = password_hash
        user.salt = salt
        user.question = question
        user.answer_hash = answer_hash
        users.append(user)
    return users


def add_user(user):
    # only a Pax has a phone and only a Driver has a permit_no
    phone = ""
    permit_no = ""
    if user.role == "pax":
        phone = user.phone
    elif user.role == "driver":
        permit_no = user.permit_no

    run("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user.username, user.role, user.name, phone, permit_no,
         user.password_hash, user.salt, user.question, user.answer_hash))


def update_user(user):
    # used when a password is reset. WHERE picks the one row to change.
    run("""UPDATE users
           SET password_hash = ?, salt = ?, question = ?, answer_hash = ?
           WHERE username = ?""",
        (user.password_hash, user.salt, user.question, user.answer_hash, user.username))


# ---------- vehicles ----------

def load_vehicles():
    vehicles = []
    for row in fetch("SELECT plate, make, model, seats, driver_username FROM vehicles"):
        plate, make, model, seats, driver_username = row
        vehicles.append(Vehicle(plate, make, model, seats, driver_username))
    return vehicles


def add_vehicle(vehicle):
    run("INSERT INTO vehicles VALUES (?, ?, ?, ?, ?)",
        (vehicle.plate, vehicle.make, vehicle.model, vehicle.seats, vehicle.driver_username))


def update_vehicle(vehicle):
    # a driver has one vehicle, so the driver's username finds the row.
    # (We cannot use the plate to find it, the plate may be what changed.)
    run("""UPDATE vehicles
           SET plate = ?, make = ?, model = ?, seats = ?
           WHERE driver_username = ?""",
        (vehicle.plate, vehicle.make, vehicle.model, vehicle.seats, vehicle.driver_username))


# ---------- destinations ----------

def load_destinations():
    destinations = []
    for row in fetch("SELECT name, fare FROM destinations"):
        name, fare = row
        destinations.append(Destination(name, fare))
    return destinations


def add_destination(destination):
    run("INSERT INTO destinations VALUES (?, ?)", (destination.name, destination.fare))


# ---------- bookings ----------

def load_bookings():
    bookings = []
    rows = fetch("""SELECT booking_id, pax_username, pickup, destination,
                           fare, status, driver_username, rating
                    FROM bookings ORDER BY booking_id""")
    for row in rows:
        booking_id, pax_username, pickup, destination, fare, status, driver_username, rating = row
        bookings.append(Booking(booking_id, pax_username, pickup, destination,
                                fare, status, driver_username, rating))
    return bookings


def add_booking(booking):
    # we name the columns here and leave booking_id out, so that the
    # database chooses the number. run() gives that number back to us.
    new_id = run("""INSERT INTO bookings
                        (pax_username, pickup, destination, fare, status, driver_username, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (booking.pax_username, booking.pickup, booking.destination, booking.fare,
                  booking.status, booking.driver_username, booking.rating))
    return new_id


def update_booking(booking):
    # the three things about a booking that can change after it is made
    run("""UPDATE bookings
           SET status = ?, driver_username = ?, rating = ?
           WHERE booking_id = ?""",
        (booking.status, booking.driver_username, booking.rating, booking.booking_id))

# TRY: run the app once, then look inside the database from a terminal:
#          sqlite3 data/uba.db
#          .tables
#          SELECT username, role, password_hash FROM users;
#          .quit
#      Can you tell what anyone's password is?
