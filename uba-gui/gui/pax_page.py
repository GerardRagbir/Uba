# ============================================================
# STOP 5 of 7 - pax_page.py - what a passenger sees after logging in
# You came from: gui/login_page.py   Next stop: gui/driver_page.py
# ============================================================
# The same pattern as the login page, with three new things to notice:
#     1. a box that reacts while you are choosing (update_fare)
#     2. a list drawn as a grid instead of a table (show_my_bookings)
#     3. buttons on every line of that list (ActionButton, from base_page.py)

from nicegui import ui

from models import Booking
from gui.base_page import BasePage, ActionButton


class PaxPage(BasePage):

    subtitle = "Passenger Bookings"

    def build(self):
        pax = self.session.current_user

        # ----- first get the data ready, then draw -----

        # the dropdowns need a list of names, not a list of Destination objects
        destination_names = []
        for destination in self.session.destinations:
            destination_names.append(destination.name)

        # go through the statuses in order, so pending bookings come first
        # and finished ones (completed or cancelled) end up at the bottom
        # NOTICE: this is sorting done with two plain loops, no sort() needed.
        my_bookings = []
        for status in ["pending", "accepted", "completed", "cancelled"]:
            for booking in self.session.bookings:
                if booking.pax_username == pax.username and booking.status == status:
                    my_bookings.append(booking)

        # ----- now draw the three tabs -----

        with self.make_tabs(["Book a ride", "My bookings", "Destinations and fares"]):

            with ui.tab_panel("Book a ride").classes("items-center"):
                # a card is a box with a border and a shadow
                with ui.card().classes("w-96 p-6"):
                    ui.label("Where are you going?").classes("text-lg font-bold")

                    # a row holding an icon and a dropdown side by side
                    with ui.row().classes("w-full items-center no-wrap"):
                        ui.icon("trip_origin", color="primary").classes("text-2xl")
                        # NOTICE: on_change is like on_click, but it runs
                        # every time a different choice is picked.
                        self.pickup = ui.select(destination_names, label="Pickup",
                                                on_change=self.update_fare).props("outlined").classes("grow")

                    with ui.row().classes("w-full items-center no-wrap"):
                        ui.icon("place", color="red").classes("text-2xl")
                        self.destination = ui.select(destination_names, label="Destination",
                                                     on_change=self.update_fare).props("outlined").classes("grow")

                    ui.separator()   # a thin line across the card

                    # kept in a self. variable so update_fare can change its text
                    self.fare_label = ui.label("Choose a pickup and a destination to see the fare.")
                    ui.button("Book ride", icon="local_taxi", on_click=self.book_ride).classes("w-full")

            with ui.tab_panel("My bookings").classes("items-center"):
                self.show_my_bookings(my_bookings)

            with ui.tab_panel("Destinations and fares").classes("items-center"):
                # both helpers come from BasePage
                self.show_table(self.destination_rows())

    def show_my_bookings(self, my_bookings):
        if len(my_bookings) == 0:
            ui.label("Nothing to show yet.")
            return

        # NOTICE: we do not use show_table() here because a table cannot
        # easily hold a button. A grid can hold anything.

        # a grid with 7 columns: every 7 items make one line of the list
        with ui.grid(columns=7).classes("w-full items-center"):
            # the first 7 items are the headings
            for heading in ["Booking", "Pickup", "Destination", "Fare (TT$)", "Status", "Driver", "Actions"]:
                ui.label(heading).classes("font-bold")

            # then 7 items for each booking. The count must stay at 7,
            # otherwise the lines stop lining up.
            for booking in my_bookings:
                ui.label(str(booking.booking_id))
                ui.label(booking.pickup)
                ui.label(booking.destination)
                ui.label(str(booking.fare))
                ui.label(booking.status)
                ui.label(booking.driver_username)
                self.show_actions(booking)   # the 7th item, see below

    def show_actions(self, booking):
        # NOTICE: what goes in the Actions column depends on the status.
        # Whatever happens, this method must draw exactly ONE item.
        if booking.status == "pending":
            # only pending bookings can be cancelled
            ActionButton(self.cancel_booking, booking, text="Cancel", color="red")

        elif booking.status == "completed":
            # a finished trip can be rated with two small clickable emojis.
            # Once one is chosen, the other one is faded out.
            up_look = "text-xl"
            down_look = "text-xl"
            if booking.booking_id in self.session.ratings:
                if self.session.ratings[booking.booking_id] == "up":
                    down_look = "text-xl opacity-30"
                else:
                    up_look = "text-xl opacity-30"

            # two buttons inside one row still count as one item in the grid.
            # no-wrap keeps them side by side. "flat dense" removes the
            # button's background and padding so only the emoji shows.
            with ui.row().classes("no-wrap gap-0"):
                up = ActionButton(self.rate_up, booking, text="👍")
                up.button.props("flat dense").classes(up_look)
                down = ActionButton(self.rate_down, booking, text="👎")
                down.button.props("flat dense").classes(down_look)

        else:
            ui.label("")   # an empty item, to keep the count at 7

    def update_fare(self):
        # runs every time the pickup or the destination is changed
        # NOTICE: this is the one place where we change a small piece of the
        # screen (set_text) instead of redrawing everything with show().
        # Redrawing here would wipe the choice the user just made.
        pickup = self.session.find_destination(self.pickup.value)
        destination = self.session.find_destination(self.destination.value)
        if pickup is None or destination is None:
            self.fare_label.set_text("Choose a pickup and a destination to see the fare.")
        elif pickup.name == destination.name:
            self.fare_label.set_text("Pickup and destination cannot be the same.")
        else:
            self.fare_label.set_text(pickup.name + " to " + destination.name
                                     + " - Fare: TT$" + str(destination.fare))

    def book_ride(self):
        # compare with book_ride() in uba/main.py: the same checks

        # step 1: read the dropdowns
        pickup = self.session.find_destination(self.pickup.value)
        destination = self.session.find_destination(self.destination.value)

        # step 2: check
        if pickup is None or destination is None:
            self.message("Choose a pickup and a destination.")
            return
        if pickup.name == destination.name:
            self.message("Pickup and destination cannot be the same.")
            return

        # step 3: change the list and save
        booking_id = len(self.session.bookings) + 1
        booking = Booking(booking_id, self.session.current_user.username, pickup.name,
                          destination.name, destination.fare, "pending", "none")
        self.session.bookings.append(booking)
        self.session.save_bookings()

        # step 4: redraw and tell the user
        self.tabs.value = "My bookings"  # jump to the tab that shows the new booking
        self.show()
        self.message("Booked! Waiting for a driver to accept.")

    def cancel_booking(self, booking):
        # called by an ActionButton, which hands us its own booking
        if booking.status != "pending":
            self.message("Only pending bookings can be cancelled.")
            return
        booking.status = "cancelled"
        self.session.save_bookings()
        self.show()
        self.message("Booking cancelled.")

    # ---------- rating a finished trip ----------
    # NOTICE: the two thumbs call two small methods, and both hand over to
    # save_rating so the real work is written once.

    def rate_up(self, booking):
        self.save_rating(booking, "up")

    def rate_down(self, booking):
        self.save_rating(booking, "down")

    def save_rating(self, booking, rating):
        if booking.status != "completed":
            self.message("Only completed trips can be rated.")
            return
        # ratings is a dict: the booking number is the key. Rating the same
        # trip again simply replaces the old answer.
        self.session.ratings[booking.booking_id] = rating
        self.session.save_ratings()
        self.show()
        self.message("Thanks for rating your driver.")

# TRY: book a ride and watch which tab opens. Which line causes that?
# TRY: rate a completed trip, then open data/ratings.txt. Rate it the other
#      way and look again. Why is there still only one line for that trip?
