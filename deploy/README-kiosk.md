# Kiosk Mode — Deployment Guide

> **Target hardware:** Raspberry Pi 5 + official 7″ Touch Display 2 (1280×720 landscape)
> **OS:** Raspberry Pi OS Bookworm with labwc (Wayland compositor)
> **User:** `ubuntu`
> **App location:** `/home/ubuntu/dmzcal`
> **Virtual env:** `/home/ubuntu/dmzcal/.venv`

---

## 1. Prerequisites

Before setting up kiosk mode, make sure the app is installed in the virtual environment:

```bash
cd /home/ubuntu/dmzcal
source .venv/bin/activate
pip install -e .
```

Verify the venv exists at `/home/ubuntu/dmzcal/.venv` and that the app launches
manually without errors before proceeding.

---

## 2. Installation

1. Make the install script executable:

   ```bash
   chmod +x scripts/install-kiosk.sh
   ```

2. Run the installer:

   ```bash
   ./scripts/install-kiosk.sh
   ```

### What the script does

1. Copies the systemd user service file (`dmzcal-kiosk.service`) into
   `~/.config/systemd/user/`.
2. Runs `systemctl --user daemon-reload` so systemd picks up the new unit.
3. Enables the service with `systemctl --user enable dmzcal-kiosk.service`.
4. Enables **loginctl linger** (`loginctl enable-linger ubuntu`) so the user
   session — and all its services — start at boot without requiring a manual
   login. This is essential for kiosk mode.
5. Adds a **labwc autostart fallback**: appends
   `systemctl --user start dmzcal-kiosk.service &` to
   `~/.config/labwc/autostart`. This ensures the service is kicked when the
   labwc compositor starts, even if `graphical-session.target` is not reliably
   reached on Raspberry Pi OS.

> **Note:** All `systemctl` commands for this service require the `--user` flag.
> Without it, systemd looks for a system-wide service and will report
> "Unit dmzcal-kiosk.service could not be found."

After installation, **reboot** to confirm everything comes up automatically:

```bash
sudo reboot
```

---

## 3. How Kiosk Mode Works

- **Auto-start:** On boot, the `ubuntu` user session starts automatically and
  systemd launches the calendar app fullscreen. No login prompt, no desktop —
  just the calendar.
- **Auto-restart:** If the app crashes for any reason, systemd waits 5 seconds
  and then restarts it automatically (`Restart=on-failure`, `RestartSec=5`).
- **User experience:** The elderly user only ever sees the calendar. There is no
  taskbar, no desktop icons, and no way to accidentally close the app with a
  casual touch.

---

## 4. Exiting Kiosk Mode (for maintenance)

There are two ways to exit the calendar and reach the desktop.

### Four-Corner Tap Sequence

Tap the four corners of the screen in order. This is designed to be impossible
to trigger accidentally but easy to remember for a caretaker.

**Tap order and timing:**

1. Tap **top-left** corner
2. Wait (within 5 seconds) → tap **top-right** corner
3. Wait (within 5 seconds) → tap **bottom-right** corner
4. Wait (within 5 seconds) → tap **bottom-left** corner

```
 [1]─────────────────────[2]
  │                        │
  │                        │
  │        SCREEN          │
  │                        │
  │                        │
 [4]─────────────────────[3]
```

**Rules:**

- Each tap must land within an **80×80 pixel** zone in the respective corner.
- Each tap must occur **within 5 seconds** of the previous one.
- If you miss a tap, tap the wrong corner, or take too long, the sequence
  **resets silently** — the calendar continues as normal with no visible
  feedback.
- On a successful four-corner sequence the app exits cleanly.

### Keyboard Shortcut

1. Plug in a USB keyboard.
2. Press **Ctrl+Shift+Q**.
3. The app exits immediately.

---

## 5. After Exiting

Once the calendar app exits:

- The **labwc desktop** appears (the Wayland compositor).
- You can open a terminal, connect to Wi-Fi, update software, edit
  configuration files, etc.

### Restarting kiosk mode

Either restart the service manually:

```bash
systemctl --user start dmzcal-kiosk.service
```

Or simply reboot:

```bash
sudo reboot
```

---

## 6. Managing the Service

All commands run as the `ubuntu` user (no `sudo` needed for `--user` units).

| Action               | Command                                                  |
| -------------------- | -------------------------------------------------------- |
| Check status         | `systemctl --user status dmzcal-kiosk.service`           |
| View logs            | `journalctl --user -u dmzcal-kiosk.service`              |
| Stop the app         | `systemctl --user stop dmzcal-kiosk.service`             |
| Disable permanently  | `systemctl --user disable dmzcal-kiosk.service`          |
| Re-enable on boot    | `systemctl --user enable dmzcal-kiosk.service`           |

### Useful log options

```bash
# Follow logs in real time
journalctl --user -u dmzcal-kiosk.service -f

# Show only the last 50 lines
journalctl --user -u dmzcal-kiosk.service -n 50

# Show logs since last boot
journalctl --user -u dmzcal-kiosk.service -b
```

---

## 7. Troubleshooting

### "Unit dmzcal-kiosk.service could not be found"

This means you ran `systemctl` without the `--user` flag. All commands for this
service **must** include `--user`:

```bash
# Wrong — looks for a system-wide service:
systemctl status dmzcal-kiosk.service

# Correct — looks in your user session:
systemctl --user status dmzcal-kiosk.service
```

### App doesn't start on boot

1. Check the service status:

   ```bash
   systemctl --user status dmzcal-kiosk.service
   ```

2. Look at the logs for error messages:

   ```bash
   journalctl --user -u dmzcal-kiosk.service -b
   ```

3. Make sure the venv exists and the app is installed:

   ```bash
   /home/ubuntu/dmzcal/.venv/bin/python -c "import dmzcal; print('OK')"
   ```

4. Verify lingering is enabled:

   ```bash
   loginctl show-user ubuntu | grep Linger
   ```

   If it says `Linger=no`, fix it with:

   ```bash
   sudo loginctl enable-linger ubuntu
   ```

5. Check that the labwc autostart fallback is in place:

   ```bash
   cat ~/.config/labwc/autostart
   ```

   It should contain a line like:

   ```
   systemctl --user start dmzcal-kiosk.service &
   ```

   If missing, re-run `./scripts/install-kiosk.sh` or add the line manually.

### Touch taps not registering

- The four-corner exit sequence requires accurate touch input. If taps seem
  offset or unresponsive, the touch display may need calibration.
- See [pi-touch-fix.md](../pi-touch-fix.md) for touch calibration instructions
  specific to the Raspberry Pi 7″ Touch Display 2.

### Service restarts in a loop

If the service keeps restarting every 5 seconds, the app is crashing
immediately on launch.

1. Stop the service so it isn't cycling:

   ```bash
   systemctl --user stop dmzcal-kiosk.service
   ```

2. Try launching the app manually to see the error:

   ```bash
   source /home/ubuntu/dmzcal/.venv/bin/activate
   cd /home/ubuntu/dmzcal
   python -m dmzcal
   ```

3. Fix the underlying issue (missing dependency, config error, etc.) and then
   restart:

   ```bash
   systemctl --user start dmzcal-kiosk.service
   ```
