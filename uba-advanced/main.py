# ============================================================
# STOP 1 of 10 - main.py - starts the app
# Read README.md first.          Next stop: security.py
# ============================================================
# Run with: python3 main.py
#
# NOTICE: this is the uba-gui app with a new data layer underneath it.
# The screens are the same. What is new is on the trail before the gui
# folder: security.py, models.py and database.py.

from nicegui import ui

import database
from gui.session import Session
from gui.login_page import LoginPage


def start():
    # NOTICE: this function runs each time the app is opened in the browser,
    # so opening the address again gives a fresh start on the login screen.

    # 1. load the data from the database (Stop 5 shows how)
    session = Session()

    # 2. make one empty area in the middle of the window. Every page draws
    #    itself inside this same area. The words in .classes() are styling
    #    words, see the README.
    container = ui.column().classes("w-full max-w-5xl mx-auto p-4")

    # 3. make the login page and tell it to draw itself (Stops 6 and 7)
    LoginPage(session, container).show()


if __name__ == "__main__":
    # make the database file and its tables if they are not there yet
    database.setup()

    # start is given without brackets: NiceGUI calls it for us later.
    # reload=False means the app does not restart itself when a file changes,
    # so after editing the code, stop it with Ctrl+C and run it again.
    ui.run(start, title="UBA Taxi Booking", reload=False)
