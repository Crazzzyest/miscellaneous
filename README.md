# Leisure Rentals — Flutter App

A mobile app for booking golf carts and sauna sessions.

## What the app does

- **Home screen** — two big colourful cards, one for Golf Cart rental (green) and one for Sauna rental (orange/red).
- **Booking screen** (one for each rental type) — tap to pick a date from a calendar, choose a start time, pick how long you need it, and adjust the number of carts or people. A price summary appears automatically once everything is filled in.
- **Confirmation screen** — shows all your booking details with an animated checkmark and a booking reference number.

## Pricing

| Rental | Price |
|--------|-------|
| Golf cart | $25 per cart, per hour (up to 4 carts) |
| Sauna | $30 per hour flat rate (up to 8 people, whole sauna reserved) |

---

## How to run this on your computer

### Step 1 — Install Flutter

Flutter is the free toolkit that turns this code into an actual phone app.

1. Go to **https://flutter.dev/docs/get-started/install**
2. Pick your computer type (Windows / Mac / Linux) and follow the steps.
3. When it says to run `flutter doctor` in a terminal, do that — it checks everything is set up.

### Step 2 — Get the code onto your computer

If you have Git installed, open a terminal and run:
```
git clone <this repo URL>
cd miscellaneous
```

Or just download the ZIP from GitHub and unzip it.

### Step 3 — Download the app's dependencies

In the terminal, inside the project folder, run:
```
flutter pub get
```
This is like telling Flutter "go and fetch everything this project needs".

### Step 4 — Run the app

Plug in an Android or iPhone, or open the Android emulator / iOS Simulator, then:
```
flutter run
```
Flutter will build the app and launch it on your device.

To run it as a web page in your browser instead:
```
flutter run -d chrome
```

---

## File map (what each file does)

```
pubspec.yaml                        ← Project config & dependency list
lib/
  main.dart                         ← App entry point; sets theme colours
  screens/
    home_screen.dart                ← Main menu with the two rental cards
    golf_cart_screen.dart           ← Golf cart booking form
    sauna_screen.dart               ← Sauna booking form
    confirmation_screen.dart        ← "You're all set!" page after booking
  widgets/
    booking_widgets.dart            ← Reusable UI pieces (date picker tile,
                                       time chips, duration chips, counter,
                                       price summary card)
```
