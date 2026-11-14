# ============================================================
# STOP 7 of 10 - login_page.py - log in, register, or reset a password
# You came from: gui/base_page.py   Next stop: gui/pax_page.py
# ============================================================
# This is the smallest complete page, so learn the pattern here.
# A page is a class with:
#     build()             draws the screen
#     one method each     for every button on it
#
# New in this version: a security question when registering, and a third
# tab, "Forgot password", that uses it.

from nicegui import ui

import security
from models import Pax, Driver, Admin
from gui.base_page import BasePage
from gui.pax_page import PaxPage
from gui.driver_page import DriverPage
from gui.admin_page import AdminPage


class LoginPage(BasePage):   # (BasePage) = inherit the header, tabs, messages

    def build(self):
        # NOTICE: we never wrote show() or header() in this class, yet this
        # page has a heading. They come from BasePage.
        with self.make_tabs(["Log in", "Register", "Forgot password"]):

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

                # asked for now, used later if the password is forgotten
                self.new_question = ui.select(security.SECURITY_QUESTIONS,
                                              value=security.SECURITY_QUESTIONS[0],
                                              label="Security question").classes("w-64")
                self.new_answer = ui.input("Your answer").classes("w-64")

                ui.button("Register", on_click=self.register)

            with ui.tab_panel("Forgot password").classes("items-center"):
                ui.label("Reset your password").classes("font-bold")
                self.forgot_username = ui.input("Username").classes("w-64")
                ui.button("Show my security question", on_click=self.show_question).props("flat")

                # kept in a self. variable so show_question can change its text
                self.question_label = ui.label("Enter your username, then press the button above.")

                self.forgot_answer = ui.input("Your answer").classes("w-64")
                self.forgot_password = ui.input("New password", password=True).classes("w-64")
                ui.button("Reset password", on_click=self.reset_password)

    def update_register_form(self):
        # runs every time the account type is changed
        role = self.new_role.value
        self.new_phone.set_visibility(role == "Passenger")
        self.new_permit.set_visibility(role == "Driver")

    # ---------- log in ----------

    def login(self):
        # step 1: read the boxes (.value is what the user typed)
        # step 2: check, and stop with a message if something is wrong
        user = self.session.find_user(self.clean(self.username.value))

        # NOTICE: check_password hashes what was typed and compares hashes.
        # This page never sees a saved password, because there is not one.
        # The password is not cleaned: spaces in a password are allowed.
        if user is None or not user.check_password(self.password.value):
            # the same message for a wrong username and a wrong password,
            # so that a stranger cannot find out which usernames exist
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

    # ---------- register ----------

    def register(self):
        # NOTICE: the four steps from the README. You will see this same
        # shape in every action method on every page.

        # step 1: read the boxes
        username = self.clean(self.new_username.value)
        password = self.new_password.value
        name = self.clean(self.new_name.value)
        answer = self.clean(self.new_answer.value)

        # step 2: check, and stop with a message if something is wrong
        if username == "" or self.session.find_user(username) is not None:
            self.message("That username is blank or already taken.")
            return
        problem = security.password_problem(password)
        if problem != "":
            self.message(problem)
            return
        if answer == "":
            self.message("Answer the security question. You need it if you forget your password.")
            return

        # step 3: make the object and save it
        # NOTICE: inheritance at work. Three different classes, but all of
        # them are users, so all of them can be handed to add_user(), and
        # all of them have set_password() and set_security_answer().
        role = self.new_role.value
        if role == "Passenger":
            new_user = Pax(username, name, self.clean(self.new_phone.value))
        elif role == "Driver":
            new_user = Driver(username, name, self.clean(self.new_permit.value))
        else:
            new_user = Admin(username, name)
        new_user.set_password(password)
        new_user.set_security_answer(self.new_question.value, answer)
        self.session.add_user(new_user)

        # step 4: redraw the page, then tell the user
        self.tabs.value = "Log in"  # jump to the log in tab
        self.show()
        self.message("Account created. You can now log in.")

    # ---------- forgot password ----------
    # NOTICE: we cannot tell the user their old password, because we do not
    # have it. All we can do is let them prove who they are another way and
    # then choose a new one.

    def show_question(self):
        user = self.session.find_user(self.clean(self.forgot_username.value))
        if user is None or user.question == "":
            self.question_label.set_text("No security question found for that username.")
        else:
            # set_text changes this one label. Redrawing the page here would
            # wipe the username that was just typed.
            self.question_label.set_text(user.question)

    def reset_password(self):
        # step 1: read the boxes
        user = self.session.find_user(self.clean(self.forgot_username.value))
        answer = self.clean(self.forgot_answer.value)
        new_password = self.forgot_password.value

        # step 2: check
        if user is None or not user.check_answer(answer):
            self.message("That answer does not match.")
            return
        problem = security.password_problem(new_password)
        if problem != "":
            self.message(problem)
            return

        # step 3: change the object and save it
        user.set_password(new_password)
        self.session.update_user(user)

        # step 4: redraw and tell the user
        self.tabs.value = "Log in"
        self.show()
        self.message("Password changed. You can now log in.")

# TRY: register an account, then use Forgot password to change its password.
#      Log in with the old password, then with the new one.
# TRY: the starter accounts all answer "arima" to their security question.
#      Reset the admin's password. Why is that a problem, and how would a
#      real app stop a stranger from doing it?
