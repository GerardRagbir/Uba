# ============================================================
# STOP 4 of 7 - login_page.py - log in, or register a new account
# You came from: gui/base_page.py   Next stop: gui/pax_page.py
# ============================================================
# This is the smallest complete page, so learn the pattern here.
# A page is a class with:
#     build()             draws the screen
#     one method each     for every button on it
#
# Compare with login() and register_pax() in uba/main.py. The checks are
# the same. Only the input() and print() lines have been swapped out.

from nicegui import ui

from models import Pax, Driver, Admin
from gui.base_page import BasePage
from gui.pax_page import PaxPage
from gui.driver_page import DriverPage
from gui.admin_page import AdminPage


class LoginPage(BasePage):   # (BasePage) = inherit the header, tabs, messages

    def build(self):
        # NOTICE: we never wrote show() or header() in this class, yet this
        # page has a heading. They come from BasePage.
        with self.make_tabs(["Log in", "Register"]):

            with ui.tab_panel("Log in").classes("items-center"):
                # NOTICE: each box is kept in a self. variable so that the
                # login() method below can read what was typed into it.
                self.username = ui.input("Username").classes("w-64")
                self.password = ui.input("Password", password=True).classes("w-64")

                # self.login has no brackets: "call this when clicked"
                ui.button("Log in", on_click=self.login)

            with ui.tab_panel("Register").classes("items-center"):
                ui.label("Create an account").classes("font-bold")
                # the kind of account decides which class we make in register()
                self.new_role = ui.select(["Passenger", "Driver", "Admin"], value="Passenger",
                                          label="Account type",
                                          on_change=self.update_register_form).classes("w-64")
                self.new_username = ui.input("Choose a username").classes("w-64")
                self.new_password = ui.input("Choose a password", password=True).classes("w-64")
                self.new_name = ui.input("Full name").classes("w-64")

                # NOTICE: these two boxes match the extra attribute each
                # child class adds in models.py: a Pax has a phone, a Driver
                # has a permit_no, and an Admin adds nothing. Both boxes are
                # drawn, and only the one that fits the account type is shown.
                self.new_phone = ui.input("Phone number").classes("w-64")
                self.new_permit = ui.input("Driver's permit number").classes("w-64")
                self.new_permit.set_visibility(False)   # hidden until Driver is chosen

                ui.button("Register", on_click=self.register)

    def update_register_form(self):
        # runs every time the account type is changed
        role = self.new_role.value
        self.new_phone.set_visibility(role == "Passenger")
        self.new_permit.set_visibility(role == "Driver")

    def login(self):
        # step 1: read the boxes (.value is what the user typed)
        # step 2: check, and stop with a message if something is wrong
        user = self.session.find_user(self.clean(self.username.value))
        if user is None or not user.check_password(self.clean(self.password.value)):
            self.message("Wrong username or password.")
            return

        # remember who is logged in. Every later page reads this.
        self.session.current_user = user

        # the user's role decides which page they get
        # NOTICE: the new page is given the SAME session and the SAME
        # container, so it draws itself where the login page used to be.
        if user.role == "pax":
            PaxPage(self.session, self.container).show()
        elif user.role == "driver":
            DriverPage(self.session, self.container).show()
        elif user.role == "admin":
            AdminPage(self.session, self.container).show()

    def register(self):
        # NOTICE: the four steps from README section 5. You will see this
        # same shape in every action method on every page.

        # step 1: read the boxes
        username = self.clean(self.new_username.value)

        # step 2: check, and stop with a message if something is wrong
        if username == "" or self.session.find_user(username) is not None:
            self.message("That username is blank or already taken.")
            return
        password = self.clean(self.new_password.value)
        name = self.clean(self.new_name.value)

        # step 3: change the list and save it to the file
        # NOTICE: inheritance at work. Three different classes, but all of
        # them are users, so all of them go into the same users list and
        # are saved by the same save_users().
        role = self.new_role.value
        if role == "Passenger":
            new_user = Pax(username, password, name, self.clean(self.new_phone.value))
        elif role == "Driver":
            new_user = Driver(username, password, name, self.clean(self.new_permit.value))
        else:
            new_user = Admin(username, password, name)
        self.session.users.append(new_user)
        self.session.save_users()

        # step 4: redraw the page, then tell the user
        self.tabs.value = "Log in"  # jump to the log in tab
        self.show()
        self.message("Account created. You can now log in.")

# TRY: register with a username that is already taken. Which line stops it?
# TRY: register one account of each type, then open data/users.txt and find
#      the three new lines. How do the lines differ, and which method in
#      models.py writes each one?
