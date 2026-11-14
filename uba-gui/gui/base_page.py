# ============================================================
# STOP 3 of 7 - base_page.py - the parent class for every page
# You came from: gui/session.py   Next stop: gui/login_page.py
# ============================================================
# Spend the most time on this file. Everything that all the screens share
# is written here ONCE: the heading, the log out menu, the tabs, the pop-up
# messages and the tables. LoginPage, PaxPage, DriverPage and AdminPage all
# inherit from BasePage, so they get all of it for free.
#
# It also holds ActionButton, the small class for a button that sits on a
# line of a list. Read BasePage first and come back to it at Stop 5.
#
# This is the same idea as User in models.py: Pax, Driver and Admin inherit
# the username, password and name, and only add what is different.

from nicegui import ui


class ActionButton:
    """A button that remembers which booking it belongs to."""

    # NOTICE: the problem this class solves. Some lists have a button on
    # every line (Cancel, Accept, thumbs up). on_click only lets us name a
    # method, it does not let us say WHICH booking was clicked. So we make
    # one small object per button, and each object keeps its own booking.
    #
    # A page uses it like this:
    #     ActionButton(self.cancel_booking, booking, text="Cancel")
    # self.cancel_booking has no brackets: we are handing the method over
    # to be called later, exactly as we do with on_click.

    def __init__(self, action, booking, text="", icon=None, color="primary"):
        self.action = action     # the page method to call when clicked
        self.booking = booking   # the booking this button belongs to
        # draws it. Kept in self.button so a page can restyle it afterwards.
        self.button = ui.button(text, icon=icon, color=color, on_click=self.click)

    def click(self):
        # call the page's method and hand it our own booking
        self.action(self.booking)


class BasePage:
    """Every page inherits from this. Child pages only write their own build()."""

    # the grey text under the "UBA" heading. Each child page sets its own.
    subtitle = "Taxi Booking"  # child pages set their own

    def __init__(self, session, container):
        self.session = session      # the data and the logged in user
        self.container = container  # the area of the window the page is drawn in
        self.tabs = None            # set by make_tabs() on pages that have tabs
        self.current_tab = None     # the name of the tab that is open

    # ---------- drawing the page ----------

    def show(self):
        # NOTICE: this is the one big idea of the whole GUI (README section 5).
        # We never update one small piece of the screen. We wipe the area and
        # draw the page again from the lists in the session. Every action
        # method ends by calling self.show().

        # before wiping, remember which tab was open so we can reopen it
        if self.tabs is not None:
            self.current_tab = self.tabs.value  # remember which tab was open

        self.container.clear()
        with self.container:   # "with" = draw the next things inside the area
            self.header()      # the same on every page, written below
            self.build()       # different on every page, written by the child

    def header(self):
        user = self.session.current_user

        # a row puts things side by side. justify-between pushes the heading
        # to the left end and the welcome button to the right end.
        with ui.row().classes("w-full items-center justify-between"):
            # left side: app name with the page name under it
            # (a column puts things one under the other)
            with ui.column().classes("gap-0"):
                ui.label("UBA").classes("text-3xl font-bold")
                ui.label(self.subtitle).classes("text-gray-500")

            # right side: tap the welcome text to show the log out option.
            # On the login page nobody is logged in, so nothing is drawn.
            if user is not None:
                # NOTICE: a menu drawn inside a button opens when the button
                # is clicked. We did not have to write any code for that.
                with ui.button("Welcome, " + user.username, icon="account_circle").props("flat no-caps"):
                    with ui.menu():
                        ui.menu_item("Log out", on_click=self.logout)

    def build(self):
        # NOTICE: this is empty on purpose. Each child page writes its own
        # build() and Python uses the child's one instead (overriding).
        # show() above calls self.build() without knowing which page it is.
        pass

    # ---------- tabs ----------

    def make_tabs(self, names):
        # draws a row of tabs, the child page then fills in one panel per tab
        # A child uses it like this:
        #     with self.make_tabs(["First", "Second"]):
        #         with ui.tab_panel("First"):
        #             ...
        # The name given to ui.tab_panel must match a name in the list.

        # the first time the page is drawn, open the first tab
        if self.current_tab is None:
            self.current_tab = names[0]

        # the strip of tab buttons along the top
        self.tabs = ui.tabs(value=self.current_tab).classes("w-full")
        with self.tabs:
            for name in names:
                ui.tab(name)

        # the area under the strip. It shows the panel of whichever tab is open.
        return ui.tab_panels(self.tabs, value=self.current_tab).classes("w-full")

    # ---------- small helpers every page can use ----------

    def logout(self):
        # reloading the app starts a fresh session on the login page
        # (it runs start() in main.py again)
        ui.navigate.to("/")

    def message(self, text):
        # a small pop up message at the bottom of the window.
        # This replaces print() from the console version.
        with self.container:
            ui.notify(text)

    def clean(self, text):
        # same rule as the console app: | is the file separator, so remove it
        # An empty box can give us None, so we turn that into "" first.
        if text is None:
            return ""
        return text.strip().replace("|", "")

    # ---------- tables ----------

    def show_table(self, rows):
        # rows is a list of dicts, the dict keys become the column headings
        # For example:
        #     [{"Destination": "Arima", "Fare (TT$)": 90},
        #      {"Destination": "Couva", "Fare (TT$)": 100}]
        # gives a table with two columns and two lines.
        if len(rows) == 0:
            ui.label("Nothing to show yet.")
            return

        # the table needs to know which column tells the lines apart.
        # We use the first one (the booking number, the username, the plate).
        first_heading = list(rows[0].keys())[0]

        # tables push text to the right by default, so line every column up on the left
        ui.table(rows=rows, row_key=first_heading,
                 column_defaults={"align": "left"}).classes("w-full")

    def booking_rows(self, bookings):
        # turns a list of Booking objects into the list of dicts show_table wants
        rows = []
        for booking in bookings:
            rows.append({
                "Booking": booking.booking_id,
                "Pickup": booking.pickup,
                "Destination": booking.destination,
                "Fare (TT$)": booking.fare,
                "Status": booking.status,
                "Pax": booking.pax_username,
                "Driver": booking.driver_username,
                "Rating": self.session.rating_text(booking.booking_id),
            })
        return rows

    def destination_rows(self):
        # the same idea for the destinations. Both the passenger page and the
        # admin page show this table, which is why it is written here once.
        rows = []
        for destination in self.session.destinations:
            rows.append({"Destination": destination.name, "Fare (TT$)": destination.fare})
        return rows

# TRY: change "UBA" in header() to something else and run the app again.
#      Log in as each kind of user. Why did every screen change?
