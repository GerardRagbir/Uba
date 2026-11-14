# UBA Taxi Booking - GUI version

A note from your lecturer. Read this first, then follow the trail through the code.

In the `uba` folder we built a taxi booking app that runs in the console.
In this folder we take the same app and put a graphical screen on top of it.
The point of the exercise is to see that **we did not rewrite the app**. We kept
the classes and the file storage exactly as they were and added a new layer.

## 1. Set up and run

You need one extra library, NiceGUI. Install it once:

```
pip install nicegui
```

Then, from inside the `uba-gui` folder:

```
python3 main.py
```

A browser tab opens at `http://localhost:8080`. The app keeps running in the
terminal until you press `Ctrl+C`. Closing the browser tab does **not** stop it.

If you see `address already in use`, an older copy is still running. Go to
that terminal and press `Ctrl+C`, then start it again.

Logins to try:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Driver | `kwame` | `drive123` |
| Driver | `shiva` | `drive123` |
| Passenger | `gerard` | `pax123` |

## 2. What changed from the console version

| File | What happened to it |
|---|---|
| `models.py` | **Not changed.** Same `User`, `Pax`, `Driver`, `Admin`, `Vehicle`, `Destination`, `Booking`. |
| `storage.py` | **Not changed.** Same text files, same `load_...` and `save_all` functions. |
| `data/` | Same four text files, plus one new file, `ratings.txt`, for the thumbs up and down. |
| `main.py` | **Replaced.** It used to hold every menu, `input()` and `print()`. Now it is a few lines that start the GUI. |
| `gui/` | **New.** One file per screen. This is the layer we added. |

Compare `uba/main.py` with the files in `gui/`. Every `input()` became a text
box or a dropdown. Every `print()` became a label, a table or a pop-up message.
Every menu choice became a button or a tab. The `if` checks in the middle are
the same ones you already wrote.

## 3. The trail - read the files in this order

Each file starts with a `STOP` comment that tells you where you came from and
where to go next. Inside the files, look for comments that start with `NOTICE`
(something worth understanding) and `TRY` (something to change and re-run).

| Stop | File | What to look for |
|---|---|---|
| 1 | `main.py` | How the app starts. It is only three real lines. |
| 2 | `gui/session.py` | Where the lists of users, vehicles, destinations and bookings live, and the dict of ratings. |
| 3 | `gui/base_page.py` | The parent class. **Spend the most time here.** |
| 4 | `gui/login_page.py` | The first child page. The smallest full example. |
| 5 | `gui/pax_page.py` | The passenger screen. Buttons on every line of a list, and rating a trip. |
| 6 | `gui/driver_page.py` | The driver screen. An `if` decides what is drawn, and a form edits an existing object. |
| 7 | `gui/admin_page.py` | Same pattern, split into one method per tab. |

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
and draws the whole page again from the lists in the session. That is the GUI
version of the console app printing the menu again after every choice.

Every action method therefore has the same four steps:

1. read the values from the boxes
2. check them with `if` and stop with a message if something is wrong
3. change the list and save it to the file
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

## 8. Exercises

Start at the top. Each one is a little harder than the one before.

1. Change the subtitle of the driver page.
2. On the passenger page, add a fourth tab called "Help" with two labels in it.
3. On the admin Users tab, show the user's password length as a new column.
4. On the admin Bookings tab, show only the pending bookings.
5. On the driver's Past bookings table, add a column showing the passenger's
   phone number.
6. Let a passenger cancel a booking that has been accepted, not only a pending
   one. What should happen to the driver's current job?
7. On the driver page, show how many thumbs up and thumbs down the driver has
   in total.
8. Add an admin action to remove a destination.

## 9. Things this version does not do well

Be ready to discuss these.

- **The rules are written twice.** The checks in `uba/main.py` are mixed in with
  `input()` and `print()`, so the GUI could not reuse them and repeats them. How
  would you organise the console version so that both could share one copy?
- **Passwords are stored as plain text** in `data/users.txt`.
- **Anyone can register as an admin** from the Register tab. That keeps testing
  easy, but a real app would never allow it. Who should be able to create an
  admin, and where would you put that check?
- **Ratings live in their own file** because we chose not to change `Booking`
  in `models.py`. Would it be better as an attribute of `Booking`? What would
  have to change if we moved it?
- **Two people using the app at once do not see each other's changes** until
  they log in again, because each session loads the files once at the start.
- **Booking numbers** come from the length of the list. What breaks if a booking
  is ever deleted?
- **Everything is saved by rewriting the whole file.** This is one reason we
  move to sqlite3 next. When we do, only `storage.py` should need to change.
