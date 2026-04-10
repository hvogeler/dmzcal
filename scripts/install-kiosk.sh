#!/usr/bin/env bash
# install-kiosk.sh — Install and enable the dmzcal kiosk systemd user service.
#
# This script:
#   1. Copies the dmzcal-kiosk.service unit file into the user's systemd directory
#   2. Reloads the daemon and enables the service
#   3. Enables loginctl linger so the user session starts at boot (no manual login needed)
#   4. Sets up a labwc autostart entry as a belt-and-suspenders fallback
#
# Make this script executable before running:
#   chmod +x scripts/install-kiosk.sh

set -euo pipefail

# ---------------------------------------------------------------------------
# Determine the project root directory.
# The script lives in <project_root>/scripts/, so we go one level up.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SERVICE_NAME="dmzcal-kiosk.service"
SOURCE_SERVICE="${PROJECT_ROOT}/deploy/${SERVICE_NAME}"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
DEST_SERVICE="${SYSTEMD_USER_DIR}/${SERVICE_NAME}"
LABWC_AUTOSTART_DIR="${HOME}/.config/labwc"
LABWC_AUTOSTART="${LABWC_AUTOSTART_DIR}/autostart"
DMZCAL_BIN="${PROJECT_ROOT}/.venv/bin/dmzcal"

echo "=== dmzcal Kiosk Service Installer ==="
echo ""
echo "Project root : ${PROJECT_ROOT}"
echo "Service file : ${SOURCE_SERVICE}"
echo "Install to   : ${DEST_SERVICE}"
echo ""

# ---------------------------------------------------------------------------
# Verify the source service file exists.
# ---------------------------------------------------------------------------
if [[ ! -f "${SOURCE_SERVICE}" ]]; then
    echo "ERROR: Service file not found at ${SOURCE_SERVICE}" >&2
    echo "       Make sure you are running this script from the project repository." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Verify the dmzcal binary exists in the venv.
# ---------------------------------------------------------------------------
if [[ ! -x "${DMZCAL_BIN}" ]]; then
    echo "WARNING: ${DMZCAL_BIN} not found or not executable."
    echo "         Make sure you have run: pip install -e . (inside the venv)"
    echo ""
fi

# ---------------------------------------------------------------------------
# Create the systemd user directory if it doesn't already exist.
# ---------------------------------------------------------------------------
if [[ ! -d "${SYSTEMD_USER_DIR}" ]]; then
    echo "Creating systemd user directory: ${SYSTEMD_USER_DIR}"
    mkdir -p "${SYSTEMD_USER_DIR}"
else
    echo "Systemd user directory already exists."
fi

# ---------------------------------------------------------------------------
# Copy the service file into place.
# ---------------------------------------------------------------------------
echo "Copying ${SERVICE_NAME} to ${SYSTEMD_USER_DIR}/ ..."
cp "${SOURCE_SERVICE}" "${DEST_SERVICE}"
echo "Service file installed."

# ---------------------------------------------------------------------------
# Reload systemd so it picks up the new/updated unit file.
# ---------------------------------------------------------------------------
echo "Reloading systemd user daemon ..."
systemctl --user daemon-reload
echo "Daemon reloaded."

# ---------------------------------------------------------------------------
# Enable the service so it starts automatically on login/reboot.
# ---------------------------------------------------------------------------
echo "Enabling ${SERVICE_NAME} ..."
systemctl --user enable "${SERVICE_NAME}"
echo "Service enabled."

# ---------------------------------------------------------------------------
# Enable loginctl linger so the user session (and its services) start at
# boot without requiring a manual login.  This is essential for kiosk mode.
# ---------------------------------------------------------------------------
CURRENT_USER="$(whoami)"
echo ""
echo "Enabling loginctl linger for user '${CURRENT_USER}' ..."
echo "(This ensures your user session starts at boot, even without a login.)"
if command -v loginctl &>/dev/null; then
    # loginctl enable-linger requires either root or polkit authorisation.
    # Try without sudo first; fall back to sudo if it fails.
    if loginctl enable-linger "${CURRENT_USER}" 2>/dev/null; then
        echo "Linger enabled for '${CURRENT_USER}'."
    elif sudo loginctl enable-linger "${CURRENT_USER}"; then
        echo "Linger enabled for '${CURRENT_USER}' (via sudo)."
    else
        echo "WARNING: Could not enable linger. You may need to run manually:"
        echo "    sudo loginctl enable-linger ${CURRENT_USER}"
    fi
else
    echo "WARNING: loginctl not found. Linger could not be enabled."
    echo "         The service may not start automatically at boot."
fi

# ---------------------------------------------------------------------------
# Set up labwc autostart as a fallback.
#
# On Raspberry Pi OS Bookworm with labwc, the graphical-session.target may
# not always be reached reliably for user services.  Adding a line to
# labwc's autostart file ensures the systemd service is kicked if it hasn't
# started yet.
# ---------------------------------------------------------------------------
echo ""
echo "Setting up labwc autostart fallback ..."

if [[ ! -d "${LABWC_AUTOSTART_DIR}" ]]; then
    mkdir -p "${LABWC_AUTOSTART_DIR}"
fi

AUTOSTART_LINE="systemctl --user start ${SERVICE_NAME} &"

if [[ -f "${LABWC_AUTOSTART}" ]] && grep -qF "${SERVICE_NAME}" "${LABWC_AUTOSTART}"; then
    echo "labwc autostart already contains a ${SERVICE_NAME} entry — skipping."
else
    # Append to existing autostart (or create it).
    echo "" >> "${LABWC_AUTOSTART}"
    echo "# Start dmzcal kiosk calendar" >> "${LABWC_AUTOSTART}"
    echo "${AUTOSTART_LINE}" >> "${LABWC_AUTOSTART}"
    echo "Added '${AUTOSTART_LINE}' to ${LABWC_AUTOSTART}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "✔ Installation complete!"
echo ""
echo "  Autostart methods configured:"
echo "    1. systemd user service (${SERVICE_NAME})"
echo "    2. labwc autostart fallback (${LABWC_AUTOSTART})"
echo "    3. loginctl linger (user session starts at boot)"
echo ""
echo "  The calendar will start automatically on next reboot."
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# Optionally start the service right now.
# ---------------------------------------------------------------------------
read -rp "Would you like to start the service now? [y/N] " answer
case "${answer}" in
    [yY]|[yY][eE][sS])
        echo "Starting ${SERVICE_NAME} ..."
        systemctl --user start "${SERVICE_NAME}"
        echo "✔ Service started. Check status with:"
        echo "    systemctl --user status ${SERVICE_NAME}"
        ;;
    *)
        echo "Skipping immediate start. You can start it manually later with:"
        echo "    systemctl --user start ${SERVICE_NAME}"
        ;;
esac

echo ""
echo "Done. Reboot to verify kiosk mode: sudo reboot"
