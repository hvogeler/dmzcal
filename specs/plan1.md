# Implementation Plan — Dementia Calendar App (`dmzcal`)

## Summary of Requirements

- **Platform**: Raspberry Pi with directly-attached 7" display (1280×720, landscape)
- **UI**: Full-screen tkinter app, no window decorations
- **Display elements** (in order of prominence):
  1. **Day of the week** (German) — largest possible font, spanning full width
  2. **Special events** (holidays/birthdays) — medium font, light orange
  3. **Date** (DD.MM.YYYY, no leading zeros) — medium font, white
  4. **Time** (24h format, HH:MM) — smallest, least prominent, white
- **Colors**: White text on black background; holidays/birthdays in light orange
- **Font**: Bold sans-serif — bundled Noto Sans Bold and Roboto Bold
- **Holidays**: NRW (Nordrhein-Westfalen) public holidays — fixed + movable (Easter-based)
- **Birthdays**: Loaded from a YAML config file (`~/.config/dmzcal/birthdays.yaml`)
- **Python**: 3.14 (confirmed available in `.venv`)

---

## Module Architecture

```
src/dmzcal/
├── __init__.py          # (keep, empty)
├── __main__.py          # Entry point: from dmzcal.main import main
├── main.py              # App bootstrap: parse args, load config, launch UI
├── config.py            # YAML config loading (birthdays)
├── holidays.py          # NRW holiday calculation (fixed + Easter-based)
├── clock.py             # The tkinter full-screen clock/calendar UI
├── py.typed             # PEP 561 marker
└── fonts/               # Bundled font files
    ├── NotoSans-Bold.ttf
    └── Roboto-Bold.ttf
```

```
config/
└── birthdays.example.yaml   # Example birthday config (shipped with project)

tests/
├── conftest.py
├── test_config.py           # Tests for config loading
├── test_holidays.py         # Tests for holiday calculation
└── test_clock.py            # Tests for UI logic (formatting, display strings)
```

---

## Module Details

### 1. `config.py` — Birthday Configuration

- Load a YAML file with birthday entries
- Schema:
  ```yaml
  birthdays:
    - name: "Oma"
      month: 3
      day: 15
    - name: "Hans"
      month: 12
      day: 24
  ```
- Provide a `get_birthdays_for_date(date, config) -> list[str]` function
- Config file path: default to `~/.config/dmzcal/birthdays.yaml`, overridable via CLI arg `--config`

### 2. `holidays.py` — NRW Public Holidays

- Compute all NRW public holidays for a given year
- **Fixed holidays**:
  - Neujahr (1.1)
  - Tag der Arbeit (1.5)
  - Tag der Deutschen Einheit (3.10)
  - Allerheiligen (1.11)
  - 1. Weihnachtstag (25.12)
  - 2. Weihnachtstag (26.12)
- **Easter-based movable holidays**:
  - Karfreitag (Easter − 2)
  - Ostermontag (Easter + 1)
  - Christi Himmelfahrt (Easter + 39)
  - Pfingstmontag (Easter + 50)
  - Fronleichnam (Easter + 60)
- Easter calculation using the anonymous Gregorian algorithm (Gauss/Meeus)
- Provide `get_holiday_for_date(date) -> str | None`
- All holiday names in German

### 3. `clock.py` — Tkinter Full-Screen UI

- Full-screen window (`overrideredirect(True)`, geometry `1280x720`)
- Black background
- Layout (top to bottom):
  - **Day of week**: Largest font, white, bold sans-serif. Fixed size calculated so "Donnerstag" (longest German weekday) fits the full 1280px width
  - **Special line**: Holiday and/or birthday text, light orange (`#FFB347` or similar).
    - Holiday only: `"Karfreitag"`
    - Birthday only: `"Geburtstag: Oma"`
    - Both: `"Karfreitag - Geburtstag: Oma"`
    - Neither: line hidden / empty
  - **Date**: White, medium font. Format: `D.M.YYYY` (no leading zeros)
  - **Time**: White, smaller font. Format: `HH:MM` (24h, no seconds)
- Update every second (for time); check date change to refresh day/holiday/birthday
- Font loading: use bundled `.ttf` files via Tk's `font create` with file path (Tcl/Tk 9.0 supports this). Try Noto Sans Bold → Roboto Bold → system fallback (DejaVu Sans Bold)

### 4. `main.py` — Application Entry Point

- Parse CLI arguments:
  - `--config` / `-c`: Path to birthdays YAML file (default: `~/.config/dmzcal/birthdays.yaml`)
  - `--windowed` / `-w`: Run in windowed mode for development (not fullscreen)
- Load config
- Launch the tkinter clock UI

---

## Font Strategy

- Bundle **Noto Sans Bold** and **Roboto Bold** under `src/dmzcal/fonts/`
- Both are Google Fonts, freely available under the Open Font License (OFL)
- At startup, load the bundled `.ttf` file directly using Tk 9.0's font file support
- Try fonts in order: Noto Sans Bold → Roboto Bold → DejaVu Sans Bold (system fallback)
- Download fonts from Google Fonts during initial project setup

---

## Dependencies

### Runtime (add to `[project] dependencies` in `pyproject.toml`)
- `PyYAML` — YAML config parsing

### Dev (add to `[project.optional-dependencies] dev`)
- `types-PyYAML` — mypy stubs for PyYAML

---

## Testing Strategy

- **`test_holidays.py`**: Test all NRW holidays for known years (2025, 2026). Test Easter calculation. Test non-holiday dates return `None`.
- **`test_config.py`**: Test YAML loading, birthday matching, missing file handling, malformed YAML.
- **`test_clock.py`**: Test display string formatting (date format, special line composition, day-of-week German names). Pure logic tests — no tkinter instantiation needed.
- Target 80%+ coverage on `src/`.

---

## Implementation Order

1. **Add dependencies** (`PyYAML`, `types-PyYAML` to `pyproject.toml`; `pip install -e .`)
2. **Download and bundle fonts** (Noto Sans Bold, Roboto Bold into `src/dmzcal/fonts/`)
3. **`holidays.py`** + **`test_holidays.py`** — pure logic, no UI, easy to test
4. **`config.py`** + **`test_config.py`** — YAML loading, pure logic
5. **`clock.py`** — the tkinter UI
6. **`main.py`** + **`__main__.py`** — wire everything together
7. **Example `birthdays.example.yaml`** config file
8. **Add `py.typed`** marker
9. **Full quality pass**: mypy strict, black, isort, ruff, pytest — all green
10. **Update `pyproject.toml`** python_version to 3.14

---

## Existing Code Cleanup

The current `main.py` has placeholder functions (`hello`, `df`, `read_file`) and `test_main.py` tests those placeholders. These will be **completely replaced** with the real calendar application code.

---

## Future: Raspberry Pi Kiosk Mode

Deferred until the app itself is working. Notes for later implementation:

The tkinter app already handles its own fullscreen behavior (`overrideredirect(True)`, full 1280×720 geometry, black background). The Pi-side configuration is about ensuring the app launches automatically on boot with nothing else visible.

### Recommended approach: bare X11 (no desktop environment)

The lightest option — skip the desktop environment entirely and launch X11 with only the calendar app:

```
xinit /path/to/dmzcal -- :0
```

No window manager, no taskbar, no desktop icons. Just X11 + tkinter.

### Configuration tasks (for later)

1. **Autologin**: Configure the Pi to log in automatically (via `raspi-config` or `/etc/systemd/system/getty@tty1.service.d/`)
2. **Auto-start X + app**: Use `.bash_profile` or a systemd service to run `xinit` pointing at the app
3. **Hide mouse cursor**: Install `unclutter` to auto-hide the cursor after inactivity
4. **Disable screen blanking**: Prevent DPMS / screensaver from turning off the display (`xset s off`, `xset -dpms`)
5. **Disable screen power management**: Ensure the display stays on 24/7
6. **Watchdog**: Optionally add a systemd restart policy so the app relaunches if it crashes