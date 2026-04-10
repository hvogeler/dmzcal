# Kiosk Mode

## Requirements

This app needs to start when the Pi is turned on. It must always show whenever the device is turned on.
The elderly user must not be confronted with anything else than this day of the week screen.

However there must be some way for me to close the app and get back to the desktop to open a terminal window.

The device will be in the household of the elderly person without WIFI connection. This means I can not ssh into the device.
I would bring a wifi hub for maintenance. But to connect with that wifi hub, I need access to a terminal on the desktop.

---

## Environment

- **Device:** Raspberry Pi 5 + official 7″ Touch Display 2 (1280×720 landscape)
- **OS:** Raspberry Pi OS Bookworm
- **Compositor:** labwc (Wayland / wlroots)
- **User:** `ubuntu`
- **App location:** `/home/ubuntu/dmzcal`
- **Virtual env:** `/home/ubuntu/dmzcal/.venv`

---

## Design

### Overview

Two layers:

1. **Autostart service** — a systemd user service launches the calendar on boot and restarts it on crash
2. **In-app secret exits** — a hidden four-corner tap sequence and a keyboard shortcut to quit the app cleanly

There is no boot-time bypass. All maintenance escape happens from within the running app.

### 1. Autostart via systemd user service

A systemd **user** service starts the calendar automatically after the graphical session is ready.

```
[Unit]
Description=DMZ Dementia Calendar (Kiosk Mode)
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=/home/ubuntu/dmzcal/.venv/bin/dmzcal
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical-session.target
```

Key features:

- **`Restart=on-failure`** — if the app crashes, it comes right back within 5 seconds. The user never sees a broken state.
- Runs as user `ubuntu`, inheriting the Wayland session environment from labwc.

Installation path: `~/.config/systemd/user/dmzcal-kiosk.service`

### 2. In-app secret exit — four-corner tap sequence

A state machine tracks taps on the four corners of the screen. The caretaker must tap all four corners in a specific order, each within 5 seconds of the previous tap. The elderly user will never discover this accidentally.

**Sequence:** top-left → top-right → bottom-right → bottom-left

**Corner zones:** 80×80 px rectangles in each corner of the screen.

#### State machine

```
                          ┌─────────────────────────────────┐
                          │             IDLE                 │
                          │  (waiting for top-left tap)      │
                          └──────────────┬──────────────────┘
                                         │
                                    tap top-left
                                         │
                                         ▼
                          ┌─────────────────────────────────┐
                          │        TOP_LEFT_TAPPED          │
                          │  (waiting ≤5 s for top-right)   │
                          └──────────────┬──────────────────┘
                                         │
                                    tap top-right
                                    (within 5 s)
                                         │
                                         ▼
                          ┌─────────────────────────────────┐
                          │       TOP_RIGHT_TAPPED          │
                          │  (waiting ≤5 s for bottom-right)│
                          └──────────────┬──────────────────┘
                                         │
                                    tap bottom-right
                                    (within 5 s)
                                         │
                                         ▼
                          ┌─────────────────────────────────┐
                          │      BOTTOM_RIGHT_TAPPED        │
                          │  (waiting ≤5 s for bottom-left) │
                          └──────────────┬──────────────────┘
                                         │
                                    tap bottom-left
                                    (within 5 s)
                                         │
                                         ▼
                          ┌─────────────────────────────────┐
                          │          EXIT APP                │
                          │  (destroy window, return to      │
                          │   desktop)                       │
                          └─────────────────────────────────┘
```

**Reset rules:**

- If the 5-second timeout expires at any state → reset to **IDLE**.
- If a tap lands in the wrong corner for the current state → reset to **IDLE**.
- If a tap lands outside all corner zones → ignored (no state change).

### 3. In-app secret exit — keyboard shortcut

When a USB keyboard is plugged in, pressing **Ctrl+Shift+Q** exits the app immediately. This is simpler for the caretaker during hands-on maintenance.

### Exit flow summary

```
App is running fullscreen
  │
  ├─ Caretaker taps four corners (TL → TR → BR → BL, each within 5 s)
  │    → app exits cleanly → desktop appears
  │
  └─ Caretaker plugs in USB keyboard, presses Ctrl+Shift+Q
       → app exits cleanly → desktop appears

After exit:
  → systemd sees clean exit (exit code 0) → does NOT restart (Restart=on-failure)
  → Caretaker has full desktop access for terminal, Wi-Fi config, etc.
  → Reboot restores kiosk mode automatically
```

---

## Deliverables

| File | Purpose |
|---|---|
| `deploy/dmzcal-kiosk.service` | systemd user service unit |
| `scripts/install-kiosk.sh` | One-shot installer: copies service file, enables it, sets permissions |
| `deploy/README-kiosk.md` | Step-by-step setup & maintenance instructions for the Pi |
| Modify `src/dmzcal/clock.py` | Add four-corner tap state machine and Ctrl+Shift+Q binding |
| Modify `src/dmzcal/main.py` | Ensure clean exit code 0 on intentional exit |