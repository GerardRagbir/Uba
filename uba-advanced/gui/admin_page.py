# ============================================================
# STOP 10 of 10 - admin_page.py - what an admin sees after logging in
# You came from: gui/driver_page.py   This is the last stop.
# ============================================================
# The admin page has four tabs, so one build() method would be very long.
# NOTICE: build() is split into four smaller methods, one per tab, and each
# is followed by the action method for that tab. The "Add" forms open in a
# dialog (a pop-up window) so that the tabs themselves stay tidy.
#
# NOTICE: when a check fails we only show a message, so the pop-up stays
# open with what was typed. When it succeeds we call self.show(), which
# redraws the page, and a freshly drawn dialog starts off closed. Breaking a long method
# into named pieces like this is something to copy in your own work.
#
# When you finish this file, go to the exercises in the README.

from nicegui import ui

import security
from models import Driver, Vehicle, Destination
from gui.base_page import BasePage


class AdminPage(BasePage):

    subtitle = "Admin Dashboard"

    def build(self):
        # each build_... method below draws one tab_panel
        with self.make_tabs(["Users", "Vehicles", "Destinations", "Bookings"]):
            self.build_users()
            self.build_vehicles()
            self.build_destinations()
            self.build_bookings()

    # ---------- two helpers shared by the first three tabs ----------
    # NOTICE: Users, Vehicles and Destinations all look the same: a heading
    # with an "Add" button on the right, a table, and a pop-up form. The
    # parts that repeat are written once here and reused three times.

    def tab_heading(self, title, button_text, icon, dialog):
        # the line above a table: title on the left, "Add" button on the right
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(title).classes("text-lg font-bold")
            # dialog.open has no brackets: open the pop-up when clicked
            ui.button(button_text, icon=icon, on_click=dialog.open)

    def dialog_buttons(self, save_text, save_action, dialog):
        # the bottom line of a pop-up form: Cancel and the save button
        with ui.row().classes("w-full justify-end"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(save_text, on_click=save_action)

    # ---------- users ----------

    def build_users(self):
        # make the list of dicts that show_table wants (see base_page.py)
        rows = []
        for user in self.session.users:
            # NOTICE: users is a mixed list of Pax, Driver and Admin objects.
            # Only a Pax has a phone and only a Driver has a permit_no, so we
            # check the role before touching them.
            extra = ""
            if user.role == "pax":
                extra = "Phone: " + user.phone
            elif user.role == "driver":
                extra = "Permit: " + user.permit_no
            rows.append({"Username": user.username, "Name": user.name,
                         "Role": user.role, "Details": extra})

        with ui.tab_panel("Users").classes("items-center"):
            # the form lives in a dialog (a pop-up window). It is drawn now
            # but stays hidden until the "Add a driver" button opens it.
            self.driver_dialog = ui.dialog()
            with self.driver_dialog:
                with ui.card().classes("w-96 p-6"):
                    ui.label("Add a driver").classes("text-lg font-bold")
                    self.driver_username = ui.input("Username").classes("w-full")
                    self.driver_password = ui.input("Password", password=True).classes("w-full")
                    self.driver_name = ui.input("Full name").classes("w-full")
                    self.driver_permit = ui.input("Driver's permit number").classes("w-full")
                    self.driver_question = ui.select(security.SECURITY_QUESTIONS,
                                                     value=security.SECURITY_QUESTIONS[0],
                                                     label="Security question").classes("w-full")
                    self.driver_answer = ui.input("Their answer").classes("w-full")
                    self.dialog_buttons("Add driver", self.add_driver, self.driver_dialog)

            self.tab_heading("Users", "Add a driver", "person_add", self.driver_dialog)
            self.show_table(rows)

    def add_driver(self):
        # the same four steps as register() on the login page.
        # Put the two side by side: only the class being made is different.
        username = self.clean(self.driver_username.value)
        if username == "" or self.session.find_user(username) is not None:
            self.message("That username is blank or already taken.")
            return
        password = self.driver_password.value
        problem = security.password_problem(password)
        if problem != "":
            self.message(problem)
            return
        answer = self.clean(self.driver_answer.value)
        if answer == "":
            self.message("Answer the security question.")
            return
        name = self.clean(self.driver_name.value)
        permit_no = self.clean(self.driver_permit.value)

        driver = Driver(username, name, permit_no)
        driver.set_password(password)
        driver.set_security_answer(self.driver_question.value, answer)
        self.session.add_user(driver)
        self.show()
        self.message("Driver added.")

    # ---------- vehicles ----------

    def build_vehicles(self):
        rows = []
        for vehicle in self.session.vehicles:
            rows.append({"Plate": vehicle.plate, "Make": vehicle.make, "Model": vehicle.model,
                         "Seats": vehicle.seats, "Driver": vehicle.driver_username})

        # only drivers who do not have a vehicle yet can be chosen
        # NOTICE: the console version let the admin type any username and
        # then checked it. A dropdown that only offers valid choices means
        # the mistake cannot be made in the first place.
        free_drivers = []
        for user in self.session.users:
            if user.role == "driver" and self.session.find_vehicle_for_driver(user.username) is None:
                free_drivers.append(user.username)

        with ui.tab_panel("Vehicles").classes("items-center"):
            self.vehicle_dialog = ui.dialog()
            with self.vehicle_dialog:
                with ui.card().classes("w-96 p-6"):
                    ui.label("Add a vehicle").classes("text-lg font-bold")
                    self.vehicle_plate = ui.input("Plate (e.g. HDK 2210)").classes("w-full")
                    self.vehicle_make = ui.input("Make (e.g. Toyota)").classes("w-full")
                    self.vehicle_model = ui.input("Model (e.g. Axio)").classes("w-full")
                    # ui.number only accepts numbers. precision=0 means no decimals.
                    self.vehicle_seats = ui.number("Seats", value=4, min=1, precision=0).classes("w-full")
                    self.vehicle_driver = ui.select(free_drivers, label="Driver").classes("w-full")
                    if len(free_drivers) == 0:
                        ui.label("Every driver already has a vehicle. Add a driver first.").classes("text-gray-500")
                    self.dialog_buttons("Add vehicle", self.add_vehicle, self.vehicle_dialog)

            self.tab_heading("Vehicles", "Add a vehicle", "directions_car", self.vehicle_dialog)
            self.show_table(rows)

    def add_vehicle(self):
        # step 1: read the boxes
        plate = self.clean(self.vehicle_plate.value).upper()
        seats = self.vehicle_seats.value       # None if the box is empty
        driver_username = self.vehicle_driver.value   # None if nothing chosen

        # step 2: check, one rule at a time
        if plate == "" or seats is None or seats < 1:
            self.message("Plate or seats not valid.")
            return
        for vehicle in self.session.vehicles:
            if vehicle.plate == plate:
                self.message("That plate is already registered.")
                return
        if driver_username is None:
            self.message("Choose a driver for the vehicle.")
            return

        # step 3: make the object and save it
        make = self.clean(self.vehicle_make.value)
        model = self.clean(self.vehicle_model.value)
        # ui.number gives a number like 4.0, so int() turns it into 4
        self.session.add_vehicle(Vehicle(plate, make, model, int(seats), driver_username))

        # step 4: redraw and tell the user
        self.show()
        self.message("Vehicle added.")

    # ---------- destinations ----------

    def build_destinations(self):
        with ui.tab_panel("Destinations").classes("items-center"):
            self.destination_dialog = ui.dialog()
            with self.destination_dialog:
                with ui.card().classes("w-96 p-6"):
                    ui.label("Add a destination").classes("text-lg font-bold")
                    self.destination_name = ui.input("Destination name").classes("w-full")
                    self.destination_fare = ui.number("Fare in TT$", min=1, precision=0).classes("w-full")
                    self.dialog_buttons("Add destination", self.add_destination, self.destination_dialog)

            self.tab_heading("Destinations and fares", "Add a destination", "add_location", self.destination_dialog)
            # destination_rows() comes from BasePage. The passenger page
            # shows this very same table.
            self.show_table(self.destination_rows())

    def add_destination(self):
        name = self.clean(self.destination_name.value)
        fare = self.destination_fare.value
        if name == "" or fare is None or fare < 1:
            self.message("Name or fare not valid.")
            return
        for destination in self.session.destinations:
            # .lower() on both sides so "arima" and "Arima" count as the same
            if destination.name.lower() == name.lower():
                self.message("That destination already exists.")
                return
        self.session.add_destination(Destination(name, int(fare)))
        self.show()
        self.message("Destination added.")

    # ---------- bookings ----------

    def build_bookings(self):
        # the admin only looks at bookings, so this tab has no action method
        with ui.tab_panel("Bookings").classes("items-center"):
            with ui.row().classes("w-full"):
                ui.label("All bookings").classes("text-lg font-bold")
            self.show_table(self.booking_rows(self.session.bookings))

# TRY: add a destination as admin, log out, log in as a passenger and look
#      for it in the Pickup dropdown. Which lists and files made that work?
