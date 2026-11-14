# ============================================================
# STOP 6 of 7 - driver_page.py - what a driver sees after logging in
# You came from: gui/pax_page.py   Next stop: gui/admin_page.py
# ============================================================
# The same pattern again: get the data ready, draw the tabs, one method per
# button. Two things are worth noticing on this page:
#     1. an if statement decides WHAT is drawn: a driver who is free sees
#        the pending bookings, a driver on a job sees that job instead
#     2. a form that edits an object which already exists (My vehicle)

from nicegui import ui

from gui.base_page import BasePage, ActionButton


class DriverPage(BasePage):

    subtitle = "Driver Trips"

    def build(self):
        driver = self.session.current_user
        vehicle = self.session.find_vehicle_for_driver(driver.username)

        # ----- get the data ready -----
        # one walk through the bookings sorts them into three groups:
        #   pending       every pending booking (any driver may take one)
        #   current_job   the booking this driver has accepted, or None
        #   past          trips this driver has completed
        pending = []
        current_job = None
        past = []
        for booking in self.session.bookings:
            if booking.status == "pending":
                pending.append(booking)
            if booking.driver_username == driver.username:
                if booking.status == "accepted" and current_job is None:
                    current_job = booking
                elif booking.status == "completed":
                    past.append(booking)

        # ----- draw the two tabs -----
        with self.make_tabs(["Bookings", "My vehicle"]):

            with ui.tab_panel("Bookings").classes("items-center"):
                # NOTICE: the top half of this tab is one of two things.
                # A driver does one job at a time, so while a job is
                # accepted the pending list is hidden.
                if current_job is None:
                    ui.label("Pending bookings").classes("text-lg font-bold")
                    self.show_pending(pending)
                else:
                    self.show_current_job(current_job)

                ui.separator()

                # the bottom half is always the same
                ui.label("Past bookings").classes("text-lg font-bold")
                self.show_table(self.past_rows(past))

            with ui.tab_panel("My vehicle").classes("items-center"):
                self.show_vehicle_form(vehicle)

    # ---------- the three parts of the Bookings tab ----------

    def show_pending(self, pending):
        if len(pending) == 0:
            ui.label("Nothing to show yet.")
            return

        # a grid with 6 columns, the same idea as My bookings in pax_page.py
        with ui.grid(columns=6).classes("w-full items-center"):
            for heading in ["Booking", "Pickup", "Destination", "Fare (TT$)", "Pax", "Actions"]:
                ui.label(heading).classes("font-bold")

            for booking in pending:
                ui.label(str(booking.booking_id))
                ui.label(booking.pickup)
                ui.label(booking.destination)
                ui.label(str(booking.fare))
                ui.label(booking.pax_username)
                ActionButton(self.accept_booking, booking, text="Accept")

    def show_current_job(self, booking):
        # the booking only stores the passenger's username, so we look the
        # passenger up to show their name and phone number
        pax = self.session.find_user(booking.pax_username)

        with ui.card().classes("w-96 p-6"):
            ui.label("Current job - booking #" + str(booking.booking_id)).classes("text-lg font-bold")

            with ui.row().classes("items-center"):
                ui.icon("trip_origin", color="primary").classes("text-2xl")
                ui.label(booking.pickup)
            with ui.row().classes("items-center"):
                ui.icon("place", color="red").classes("text-2xl")
                ui.label(booking.destination)

            ui.label("Fare: TT$" + str(booking.fare))
            if pax is not None and pax.role == "pax":
                ui.label("Passenger: " + pax.name + ", " + pax.phone)

            ui.separator()
            with ui.row():
                ActionButton(self.complete_booking, booking, text="Complete trip", icon="check")
                ActionButton(self.cancel_job, booking, text="Cancel job", icon="close", color="red")

    def past_rows(self, past):
        # the list of dicts for show_table. The last column is the rating
        # the passenger gave, which the session looks up for us.
        rows = []
        for booking in past:
            rows.append({
                "Booking": booking.booking_id,
                "Pickup": booking.pickup,
                "Destination": booking.destination,
                "Fare (TT$)": booking.fare,
                "Pax": booking.pax_username,
                "Rating": self.session.rating_text(booking.booking_id),
            })
        return rows

    # ---------- the actions for a booking ----------
    # Each one is called by an ActionButton, which hands us its booking.

    def accept_booking(self, booking):
        # compare with accept_booking() in uba/main.py
        driver = self.session.current_user

        # check: a driver with no vehicle cannot take a booking
        if self.session.find_vehicle_for_driver(driver.username) is None:
            self.message("You need a vehicle before you can accept bookings.")
            return
        if booking.status != "pending":
            self.message("That booking is no longer pending.")
            return
        # check: one job at a time
        for other in self.session.bookings:
            if other.driver_username == driver.username and other.status == "accepted":
                self.message("Finish your current job first.")
                return

        # change the booking and save
        booking.status = "accepted"
        booking.driver_username = driver.username
        self.session.save_bookings()

        # redraw and tell the user. NOTICE: we do nothing here to swap the
        # pending list for the current job. build() works that out by
        # itself from the data, every time the page is drawn.
        self.show()
        self.message("Booking accepted.")

    def complete_booking(self, booking):
        driver = self.session.current_user
        if booking.driver_username != driver.username or booking.status != "accepted":
            self.message("That is not one of your accepted bookings.")
            return
        booking.status = "completed"
        self.session.save_bookings()
        self.show()
        self.message("Trip completed. Collect TT$" + str(booking.fare) + ".")

    def cancel_job(self, booking):
        driver = self.session.current_user
        if booking.driver_username != driver.username or booking.status != "accepted":
            self.message("That is not one of your accepted bookings.")
            return
        # NOTICE: the passenger still needs a ride, so the booking is not
        # cancelled. It goes back to pending for another driver to accept.
        booking.status = "pending"
        booking.driver_username = "none"
        self.session.save_bookings()
        self.show()
        self.message("Job cancelled. The booking is pending again.")

    # ---------- my vehicle ----------

    def show_vehicle_form(self, vehicle):
        if vehicle is None:
            ui.label("No vehicle assigned yet. Ask an admin.")
            return

        with ui.card().classes("w-96 p-6"):
            ui.label("My vehicle").classes("text-lg font-bold")
            # NOTICE: value= fills each box with what the vehicle has now,
            # so the driver only retypes the part that needs to change
            self.vehicle_plate = ui.input("Plate", value=vehicle.plate).classes("w-full")
            self.vehicle_make = ui.input("Make", value=vehicle.make).classes("w-full")
            self.vehicle_model = ui.input("Model", value=vehicle.model).classes("w-full")
            self.vehicle_seats = ui.number("Seats", value=vehicle.seats, min=1, precision=0).classes("w-full")
            ui.button("Save changes", icon="save", on_click=self.save_vehicle).classes("w-full")

    def save_vehicle(self):
        driver = self.session.current_user
        vehicle = self.session.find_vehicle_for_driver(driver.username)

        # step 1: read the boxes
        plate = self.clean(self.vehicle_plate.value).upper()
        seats = self.vehicle_seats.value

        # step 2: check
        if plate == "" or seats is None or seats < 1:
            self.message("Plate or seats not valid.")
            return
        for other in self.session.vehicles:
            # the plate may match our own vehicle, but nobody else's
            if other.plate == plate and other.driver_username != driver.username:
                self.message("That plate is already registered.")
                return

        # step 3: change the object and save
        # NOTICE: we do not make a new Vehicle. This one is already in the
        # list, so we change its attributes and save the list again.
        vehicle.plate = plate
        vehicle.make = self.clean(self.vehicle_make.value)
        vehicle.model = self.clean(self.vehicle_model.value)
        vehicle.seats = int(seats)
        self.session.save_vehicles()

        # step 4: redraw and tell the user
        self.show()
        self.message("Vehicle updated.")

# TRY: log in as a passenger and book a ride, log out, then log in as kwame
#      and accept it. Open data/bookings.txt after each step and watch the
#      line for that booking change.
# TRY: complete the trip, log in as the passenger and rate it, then log in
#      as kwame again. Where does the rating appear, and which file is it in?
