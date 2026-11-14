# ============================================================
# STOP 1 of 7 - main.py - starts the GUI version of the app
# Read README.md first.          Next stop: gui/session.py
# ============================================================
# Run with: python3 main.py
#
# NOTICE: in the console version this file held every menu, input() and
# print(). All of that has moved into the gui folder, one file per screen.
# What is left here only starts the app.

from nicegui import ui

from gui.session import Session
from gui.login_page import LoginPage


def start():
    # NOTICE: this function runs each time the app is opened in the browser,
    # so opening the address again gives a fresh start on the login screen.

    # 1. load the data from the text files (Stop 2 shows how)
    session = Session()

    # 2. make one empty area in the middle of the window. Every page draws
    #    itself inside this same area. The words in .classes() are styling
    #    words, see section 6 of the README.
    container = ui.column().classes("w-full max-w-5xl mx-auto p-4")

    # 3. make the login page and tell it to draw itself (Stops 3 and 4)
    LoginPage(session, container).show()


if __name__ == "__main__":
    # start is given without brackets: NiceGUI calls it for us later.
    # reload=False means the app does not restart itself when a file changes,
    # so after editing the code, stop it with Ctrl+C and run it again.
    ui.run(start, title="UBA Taxi Booking", reload=False)
