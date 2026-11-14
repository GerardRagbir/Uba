# ============================================================
# STOP 2 of 10 - security.py - keeping passwords safe
# You came from: main.py          Next stop: models.py
# ============================================================
# NOTICE: in uba and uba-gui the password was saved exactly as typed.
# Anyone who opened users.txt could read every password. Here we never
# save the password at all. We save a HASH of it.
#
# A hash is a one-way scramble:
#     "pax123"  ->  "9f2c41...e07a"     easy
#     "9f2c41...e07a"  ->  "pax123"     not possible
# To check a login we scramble what was typed in the same way and compare
# the two scrambles. We never need to know the real password.
#
# A SALT is a random piece of text made once for each user and mixed into
# the scramble. Without it, two users with the same password would have the
# same hash, and one leaked password would give away the other.

import hashlib
import secrets

# the questions a user can pick from when they register. The answer is how
# they prove who they are if they forget their password.
SECURITY_QUESTIONS = [
    "What town were you born in?",
    "What was the name of your primary school?",
    "What is your favourite food?",
]

MIN_PASSWORD_LENGTH = 6


def new_salt():
    # 32 random letters and digits, different every time it is called
    return secrets.token_hex(16)


def hash_text(text, salt):
    # scrambles the text together with the salt and returns the result as
    # a string of letters and digits. The same text and salt always give
    # the same result, which is what lets us compare at login.
    #
    # pbkdf2_hmac repeats the scramble 100000 times. That is still instant
    # for one login, but it makes guessing millions of passwords very slow.
    scrambled = hashlib.pbkdf2_hmac("sha256", text.encode(), salt.encode(), 100000)
    return scrambled.hex()


def password_problem(password):
    # returns a message saying what is wrong with a new password,
    # or "" when the password is acceptable
    if len(password) < MIN_PASSWORD_LENGTH:
        return "The password must be at least " + str(MIN_PASSWORD_LENGTH) + " characters."
    return ""

# TRY: in a Python shell, run these and compare the results:
#          import security
#          security.hash_text("pax123", "abc")
#          security.hash_text("pax123", "abc")
#          security.hash_text("pax123", "abd")
#          security.hash_text("pax124", "abc")
