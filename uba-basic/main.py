# main.py - UBA taxi booking console app
# Run with: python3 main.py

import storage
from models import Pax, Driver, Vehicle, Destination, Booking

# everything is loaded from the text files once, when the app starts
users = storage.load_users()
vehicles = storage.load_vehicles()
destinations = storage.load_destinations()
bookings = storage.load_bookings()


# ---------- small helpers ----------

def ask(prompt):
    answer = input(prompt).strip()
    return answer.replace("|", "")  # | is our file separator, so remove it


def ask_number(prompt):
    # returns a whole number, or -1 if the user did not type one
    answer = ask(prompt)
    if answer.isdigit():
        return int(answer)
    return -1


def find_user(username):
    for user in users:
        if user.username == username:
            return user
    return None


def find_booking(booking_id):
    for booking in bookings:
        if booking.booking_id == booking_id:
            return booking
    return None


def find_vehicle_for_driver(username):
    for vehicle in vehicles:
        if vehicle.driver_username == username:
            return vehicle
    return None


def show_destinations():
    print("\n--- Destinations ---")
    number = 1
    for destination in destinations:
        print(str(number) + ". ", end="")
        destination.show()
        number = number + 1


def choose_destination(prompt):
    # returns a Destination, or None if the choice was not valid
    choice = ask_number(prompt)
    if choice >= 1 and choice <= len(destinations):
        return destinations[choice - 1]
    return None


# ---------- login and register ----------

def login():
    username = ask("Username: ")
    password = ask("Password: ")
    user = find_user(username)
    if user is not None and user.check_password(password):
        print("\nWelcome, " + user.name + "!")
        return user
    print("Wrong username or password.")
    return None


def register_pax():
    print("\n--- Register as a passenger ---")
    username = ask("Choose a username: ")
    if username == "" or find_user(username) is not None:
        print("That username is blank or already taken.")
        return
    password = ask("Choose a password: ")
    name = ask("Full name: ")
    phone = ask("Phone number: ")
    users.append(Pax(username, password, name, phone))
    storage.save_all(storage.USERS_FILE, users)
    print("Account created. You can now log in.")


# ---------- pax pages ----------

def book_ride(pax):
    show_destinations()
    pickup = choose_destination("Pickup number: ")
    destination = choose_destination("Destination number: ")
    if pickup is None or destination is None:
        print("Invalid choice.")
        return
    if pickup.name == destination.name:
        print("Pickup and destination cannot be the same.")
        return

    booking_id = len(bookings) + 1
    booking = Booking(booking_id, pax.username, pickup.name, destination.name,
                      destination.fare, "pending", "none")
    bookings.append(booking)
    storage.save_all(storage.BOOKINGS_FILE, bookings)
    print("Booked! Waiting for a driver to accept.")
    booking.show()


def show_pax_bookings(pax):
    print("\n--- My bookings ---")
    for booking in bookings:
        if booking.pax_username == pax.username:
            booking.show()


def cancel_booking(pax):
    show_pax_bookings(pax)
    booking = find_booking(ask_number("Booking number to cancel: "))
    if booking is None or booking.pax_username != pax.username:
        print("Booking not found.")
        return
    if booking.status != "pending":
        print("Only pending bookings can be cancelled.")
        return
    booking.status = "cancelled"
    storage.save_all(storage.BOOKINGS_FILE, bookings)
    print("Booking cancelled.")


def pax_menu(pax):
    while True:
        print("\n=== Passenger menu ===")
        print("1. View destinations and fares")
        print("2. Book a ride")
        print("3. My bookings")
        print("4. Cancel a booking")
        print("0. Log out")
        choice = ask("Choose: ")
        if choice == "1":
            show_destinations()
        elif choice == "2":
            book_ride(pax)
        elif choice == "3":
            show_pax_bookings(pax)
        elif choice == "4":
            cancel_booking(pax)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


# ---------- driver pages ----------

def show_driver_vehicle(driver):
    vehicle = find_vehicle_for_driver(driver.username)
    if vehicle is None:
        print("No vehicle assigned yet. Ask an admin.")
    else:
        vehicle.show()


def show_pending_bookings():
    print("\n--- Pending bookings ---")
    for booking in bookings:
        if booking.status == "pending":
            booking.show()


def accept_booking(driver):
    if find_vehicle_for_driver(driver.username) is None:
        print("You need a vehicle before you can accept bookings.")
        return
    show_pending_bookings()
    booking = find_booking(ask_number("Booking number to accept: "))
    if booking is None or booking.status != "pending":
        print("That is not a pending booking.")
        return
    booking.status = "accepted"
    booking.driver_username = driver.username
    storage.save_all(storage.BOOKINGS_FILE, bookings)
    print("Booking accepted.")


def show_driver_trips(driver):
    print("\n--- My trips ---")
    for booking in bookings:
        if booking.driver_username == driver.username:
            booking.show()


def complete_booking(driver):
    show_driver_trips(driver)
    booking = find_booking(ask_number("Booking number to complete: "))
    if booking is None or booking.driver_username != driver.username or booking.status != "accepted":
        print("That is not one of your accepted bookings.")
        return
    booking.status = "completed"
    storage.save_all(storage.BOOKINGS_FILE, bookings)
    print("Trip completed. Collect TT$" + str(booking.fare) + ".")


def driver_menu(driver):
    while True:
        print("\n=== Driver menu ===")
        print("1. My vehicle")
        print("2. View pending bookings")
        print("3. Accept a booking")
        print("4. Complete a trip")
        print("5. My trips")
        print("0. Log out")
        choice = ask("Choose: ")
        if choice == "1":
            show_driver_vehicle(driver)
        elif choice == "2":
            show_pending_bookings()
        elif choice == "3":
            accept_booking(driver)
        elif choice == "4":
            complete_booking(driver)
        elif choice == "5":
            show_driver_trips(driver)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


# ---------- admin pages ----------

def show_users():
    print("\n--- Users ---")
    for user in users:
        user.show()  # each type of user shows itself in its own way


def add_driver():
    print("\n--- Add a driver ---")
    username = ask("Username: ")
    if username == "" or find_user(username) is not None:
        print("That username is blank or already taken.")
        return
    password = ask("Password: ")
    name = ask("Full name: ")
    permit_no = ask("Driver's permit number: ")
    users.append(Driver(username, password, name, permit_no))
    storage.save_all(storage.USERS_FILE, users)
    print("Driver added.")


def show_vehicles():
    print("\n--- Vehicles ---")
    for vehicle in vehicles:
        vehicle.show()


def add_vehicle():
    print("\n--- Add a vehicle ---")
    plate = ask("Plate number (e.g. HDK 2210): ").upper()
    for vehicle in vehicles:
        if vehicle.plate == plate:
            print("That plate is already registered.")
            return
    make = ask("Make (e.g. Toyota): ")
    model = ask("Model (e.g. Axio): ")
    seats = ask_number("Number of seats: ")
    driver_username = ask("Driver's username: ")

    driver = find_user(driver_username)
    if plate == "" or seats < 1:
        print("Plate or seats not valid.")
        return
    if driver is None or driver.role != "driver":
        print("No driver with that username.")
        return
    if find_vehicle_for_driver(driver_username) is not None:
        print("That driver already has a vehicle.")
        return

    vehicles.append(Vehicle(plate, make, model, seats, driver_username))
    storage.save_all(storage.VEHICLES_FILE, vehicles)
    print("Vehicle added.")


def add_destination():
    print("\n--- Add a destination ---")
    name = ask("Destination name: ")
    fare = ask_number("Fare in TT$: ")
    if name == "" or fare < 1:
        print("Name or fare not valid.")
        return
    for destination in destinations:
        if destination.name.lower() == name.lower():
            print("That destination already exists.")
            return
    destinations.append(Destination(name, fare))
    storage.save_all(storage.DESTINATIONS_FILE, destinations)
    print("Destination added.")


def show_all_bookings():
    print("\n--- All bookings ---")
    for booking in bookings:
        booking.show()


def admin_menu(admin):
    while True:
        print("\n=== Admin menu ===")
        print("1. View users")
        print("2. Add a driver")
        print("3. View vehicles")
        print("4. Add a vehicle")
        print("5. View destinations")
        print("6. Add a destination")
        print("7. View all bookings")
        print("0. Log out")
        choice = ask("Choose: ")
        if choice == "1":
            show_users()
        elif choice == "2":
            add_driver()
        elif choice == "3":
            show_vehicles()
        elif choice == "4":
            add_vehicle()
        elif choice == "5":
            show_destinations()
        elif choice == "6":
            add_destination()
        elif choice == "7":
            show_all_bookings()
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


# ---------- start of the app ----------

def run():
    while True:
        print("\n=== UBA Taxi Booking ===")
        print("1. Log in")
        print("2. Register as a passenger")
        print("0. Exit")
        choice = ask("Choose: ")
        if choice == "1":
            user = login()
            if user is not None:
                # the user's role decides which menu they get
                if user.role == "pax":
                    pax_menu(user)
                elif user.role == "driver":
                    driver_menu(user)
                elif user.role == "admin":
                    admin_menu(user)
        elif choice == "2":
            register_pax()
        elif choice == "0":
            print("Goodbye!")
            return
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    run()
