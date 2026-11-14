# UBA Taxi Booking - advanced version

A note from your lecturer. Read this first, then follow the trail through the code.

This is the third stage of the same app:

| Folder | What it is |
|---|---|
| `uba` | the console app, saving to text files |
| `uba-gui` | the same app with a graphical screen on top |
| `uba-advanced` | the same screens, with a real database underneath and safer passwords |

In stage two we changed the top layer (the screen) and left the bottom alone.
This time we do the opposite: **the screens stay, and the layer underneath is
replaced.** Watch how little of the `gui` folder had to change. That is the
reward for keeping the layers apart.

## 1. Set up and run

You need NiceGUI, the same as before. `sqlite3` comes with Python, so there is
nothing else to install.

```
pip install nicegui
```

Then, from inside the `uba-advanced` folder:

```
python3 main.py
```

A browser tab opens at `http://localhost:8080`. The app keeps running in the
terminal until you press `Ctrl+C`. Closing the browser tab does **not** stop it.

If you see `address already in use`, an older copy is still running. Go to
that terminal and press `Ctrl+C`, then start it again.

The first run creates `data/uba.db` with these starter accounts:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Driver | `kwame` | `drive123` |
| Driver | `shiva` | `drive123` |
| Passenger | `gerard` | `pax123` |

Every starter account answers `arima` to "What town were you born in?".

To start again with a clean database, stop the app and delete `data/uba.db`.

## 2. What changed from uba-gui

| File | What happened to it |
|---|---|
| `storage.py` | **Gone.** Replaced by `database.py`. |
| `database.py` | **New.** Every read and write to the sqlite3 database. The only file with SQL in it. |
| `security.py` | **New.** Password hashing and the security questions. |
| `models.py` | **Changed.** `User` keeps a password hash instead of a password. `Booking` gained a `rating`. `to_line()` and `show()` are gone. |
| `data/` | The five text files are replaced by one file, `uba.db`. |
| `gui/session.py` | **Changed.** Loads from the database, and saves one object at a time. |
| `gui/login_page.py` | **Changed.** A security question on Register, and a new "Forgot password" tab. |
| `gui/base_page.py` | **Barely changed.** One new line reloads the data before each redraw. |
| `gui/pax_page.py`, `gui/driver_page.py`, `gui/admin_page.py` | **Barely changed.** Only the lines that save. |

Open `uba-gui/gui/pax_page.py` and `uba-advanced/gui/pax_page.py` side by side
and find the differences. There are very few, and none of them are about
drawing the screen.

Four problems from the last version are now solved. Find where:

- passwords were stored as plain text
- booking numbers came from the length of the list
- every save rewrote a whole file
- two people using the app at once did not see each other's changes

## 3. The trail - read the files in this order

Each file starts with a `STOP` comment that tells you where you came from and
where to go next. Inside the files, look for comments that start with `NOTICE`
(something worth understanding) and `TRY` (something to change and re-run).

| Stop | File | What to look for |
|---|---|---|
| 1 | `main.py` | How the app starts. One new line sets up the database. |
| 2 | `security.py` | What a hash and a salt are. Short, and worth reading twice. |
| 3 | `models.py` | The same classes. Look at the four new methods on `User`. |
| 4 | `database.py` | **Spend the most time here.** Four kinds of SQL sentence. |
| 5 | `gui/session.py` | The go-between: pages on one side, the database on the other. |
| 6 | `gui/base_page.py` | The parent class for every page. |
| 7 | `gui/login_page.py` | Log in, register, and the new Forgot password tab. |
| 8 | `gui/pax_page.py` | The passenger screen. |
| 9 | `gui/driver_page.py` | The driver screen. |
| 10 | `gui/admin_page.py` | The admin screen. |

If you have already walked the `uba-gui` trail, stops 6, 8, 9 and 10 will feel
familiar. Skim them for the lines that changed.

## 4. Four NiceGUI ideas you need

**1. Everything on screen is made with `ui.something(...)`.**
`ui.label("Hello")` shows text. `ui.button("Book")` shows a button.
`ui.input("Username")` shows a text box. `ui.select([...])` shows a dropdown.

**2. `with` means "put the next things inside this one".**

```python
with ui.card():          # a box
    ui.label("Hello")    # inside the box
    ui.button("OK")      # also inside the box
ui.label("Outside")      # not indented, so outside the box
```

The indentation of the code is the layout of the screen.

**3. A button is given a method to call, without brackets.**

```python
ui.button("Log in", on_click=self.login)
```

`self.login` with no brackets means "call this later, when clicked".
`self.login()` with brackets would call it straight away, which is wrong here.

**4. We keep a box in a variable so we can read it later.**

```python
self.username = ui.input("Username")   # when drawing the page
...
self.username.value                    # later, in the button's method
```

## 5. The one big idea: redraw the page

After anything changes (a booking is made, a driver is added) the page does not
try to update one little piece. It calls `self.show()`, which wipes the screen
and reads the lists from the database again and draws the whole page from them. That is the GUI
version of the console app printing the menu again after every choice.

Every action method therefore has the same four steps:

1. read the values from the boxes
2. check them with `if` and stop with a message if something is wrong
3. make or change the object and save it to the database
4. `self.show()` to redraw, then `self.message(...)` to tell the user

Once you can see those four steps in `login_page.py`, you can read every other
page.

## 6. The styling words

The text inside `.classes("...")` and `.props("...")` is **not Python**. It is a
list of styling words, separated by spaces, that control how something looks.
You can delete any of them and the app still works; it only looks different.
Try it. These are all the ones we use:

| Word | Meaning |
|---|---|
| `w-full` | as wide as the space allows |
| `w-40`, `w-48`, `w-64`, `w-96` | a fixed width, bigger number is wider |
| `max-w-5xl` | never wider than this, even on a big screen |
| `mx-auto` | centre it left-to-right |
| `p-4`, `p-6` | padding, the space inside the edge |
| `gap-0` | no space between the items inside |
| `items-center` | line the items up on the centre |
| `justify-between` | push the items to the two ends |
| `justify-end` | push the items to the right end |
| `no-wrap` | keep the items on one line |
| `grow` | take up whatever space is left |
| `text-lg`, `text-xl`, `text-2xl`, `text-3xl` | bigger text |
| `font-bold` | bold text |
| `text-gray-500` | grey text |
| `outlined` (prop) | draw a border around a dropdown |
| `opacity-30` | faded, mostly see-through |
| `flat` (prop) | a button with no background |
| `dense` (prop) | a button with less space around its text |
| `no-caps` (prop) | do not turn the button text into capitals |

Icon names such as `"local_taxi"` and `"place"` come from Google's Material
Icons. Search "Material Icons" to browse the names.

## 7. Recipes

**Add a new tab to a page**

1. Add the tab's name to the list given to `self.make_tabs([...])`.
2. Add a `with ui.tab_panel("That same name"):` block and draw inside it.

**Add a button that does something**

1. Draw it: `ui.button("My button", on_click=self.my_action)`.
2. Write `def my_action(self):` in the same class, using the four steps above.

**Add a whole new page**

1. Copy `gui/driver_page.py` to a new file and rename the class.
2. Keep `(BasePage)` after the class name, and set your own `subtitle`.
3. Write your own `build()`.
4. In `gui/login_page.py`, import it and add one more `elif` in `login()`.

## 8. SQL in five minutes

SQL is the language used to talk to a database. A database holds **tables**. A
table has named **columns** and one **row** per object, like a spreadsheet.

| SQL | What it does | Before, in the text-file version |
|---|---|---|
| `CREATE TABLE users (...)` | makes a table | creating an empty `users.txt` |
| `INSERT INTO users VALUES (...)` | adds one row | adding a line to the file |
| `SELECT name, fare FROM destinations` | reads rows | reading every line and splitting on the bar character |
| `UPDATE bookings SET status = ? WHERE booking_id = ?` | changes matching rows | rewriting the whole file |

Two more words you will meet in `database.py`:

- `PRIMARY KEY` marks the column that identifies a row. The database refuses a
  second row with the same value.
- `AUTOINCREMENT` lets the database hand out the numbers 1, 2, 3 by itself.

**Always use `?` for values.** Never build SQL by joining strings:

```python
# WRONG - whatever the user types becomes part of the SQL
fetch("SELECT * FROM users WHERE username = '" + username + "'")

# RIGHT - the value is handed over separately and treated only as data
fetch("SELECT * FROM users WHERE username = ?", (username,))
```

The wrong way allows an attack called SQL injection.

You can look inside the database from a terminal:

```
sqlite3 data/uba.db
.tables
SELECT * FROM bookings;
.quit
```

## 9. Passwords and "Forgot password"

**We do not store passwords.** We store a *hash*: a one-way scramble of the
password. At login we scramble what was typed and compare the two scrambles.
`security.py` explains hashes and salts in its comments.

This has a consequence. If someone forgets their password, **we cannot tell
them what it was**, because we do not have it. Be suspicious of any website
that can email you your old password.

So "Forgot password" works like this:

1. When registering, the user picks a security question and gives an answer.
   The answer is hashed too.
2. On the Forgot password tab they type their username and see their question.
3. If their answer matches, they choose a new password.

Passwords must now be at least 6 characters. The rule is one function,
`password_problem()` in `security.py`, used by Register, Forgot password and
the admin's Add a driver form.

## 10. Exercises

Start at the top. Each one is a little harder than the one before.

1. Add a fourth security question.
2. Make the minimum password length 8. How many files did you change?
3. Add a rule that a password must contain at least one digit.
4. On the admin Bookings tab, show only the pending bookings.
5. Give every user a "Change password" option in the Welcome menu. It should
   ask for the current password first.
6. Let an admin remove a destination. You will need a new SQL sentence,
   `DELETE FROM destinations WHERE name = ?`, in a new function in
   `database.py`.
7. On the driver page, show the driver's total thumbs up and thumbs down.
8. After 3 wrong answers on Forgot password, refuse to continue for that
   username. Where should the count be kept so that reloading the page does
   not reset it?

## 11. Things this version does not do well

Be ready to discuss these.

- **Security questions are weak.** Your home town is not a secret. Real apps
  send a one-time link to your email or phone instead. Why is that safer?
- **The starter accounts all share one known answer**, so anyone who reads this
  file can reset the admin's password. What should happen before this app is
  used for real?
- **Nothing limits the number of guesses** at a password or a security answer.
- **Anyone can register as an admin** from the Register tab.
- **The whole database is loaded into lists** every time a page is drawn. That
  is fine for a class project. What happens with a million bookings, and which
  SQL word would let the database do the filtering for us?
