# Dementia Calendar
This project is to build a dementia calender. It runs on a raspberry pi with a 7" hdmi display attached.
It will be placed in a prominent place in the apartment of an elderly person who tends to forget what day it is.

# General Architecture
The app will be in Python 3.14. It must start when the Pi is powered on. Without asking for a Linux login or anything.

# UI
## Technical Specs
The UI will use all screen real estate. There must be nothing else visible on the display. No window decoration or menu bar. No title bar.
The UI should be in tkinter.

## View Design
The view should display the following:
- Day of the week in German (Montag, Dienstag, Mittwoch, .., Sonntag)
- Special meaning of the day - if any
    - Holiday. Fixed and moving holidays in Nordrheinwestphalen, Germany. This should be those days where shops in Nordrheinwestfalen are usually closed. 
    - Birthday. Birthday of close relatives.
- Date DD.MM.YYYY like 7.4.2026 or 31.3.2026 or 2.11.2026. No leading zeroes.
- Time in 24 hour format

Most important and most prominent is the Day of the Week. It must be the biggest possible font spanning the complete width of the screen for the longest week day name.
Remembering the day of the week is actually the main purpose of the app. 
Significantly smaller should be special meaning and date. 
Time should be even smaller and definitely the least prominent information.

# Open Questions

1. **Birthdays** — Which relatives' birthdays should be included? Is this a hardcoded list in a config file, or should there be a way to add/edit birthdays at runtime?

2. **Holiday and birthday display** — When it's a holiday, should the holiday name be shown (e.g., "Karfreitag", "Tag der Arbeit")? For birthdays, should it show whose birthday it is (e.g., "Geburtstag: Oma")?

3. **Screen resolution** — What is the resolution of the 7" HDMI display? (Common options: 800×480, 1024×600, 1280×800.)

4. **Day-of-week font sizing** — Should the font size be calculated dynamically at runtime so the longest day name ("Donnerstag") always fills the full screen width, or is a fixed large font size acceptable?

5. **Pi auto-start** — Should the deliverable include Raspberry Pi configuration (autologin, systemd service or `.xinitrc`) to launch the app on power-on, or just the Python application itself?

6. **Python version** — The spec says Python 3.14, but 3.14 is still in alpha. Should we target 3.14, or use the latest stable (3.12 or 3.13)?

7. **Color scheme** — Any preferences? High contrast is generally recommended for elderly users (e.g., white or yellow text on a dark background). Any specific colors or style?

8. **Font / typeface** — Any preferred typeface, or should we choose something clear and legible (e.g., a bold sans-serif)?

