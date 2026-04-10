# Activate venv

```
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

# Check venv

```
echo $VIRTUAL_ENV

which python
```

# Install requirements

```
pip install -r requirements-dev.txt
pip install -e .
```
# Create new venv
```
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

# Get Display resolution
```
sudo -u ubuntu XDG_RUNTIME_DIR=/run/user/$(id -u ubuntu) WAYLAND_DISPLAY=wayland-0 wlr-randr
```
```
DSI-2 "(null) (null) (DSI-2)"
  Physical size: 90x151 mm
  Enabled: yes
  Modes:
    720x1280 px, 60.037998 Hz (preferred, current)
  Position: 0,0
  Transform: 270
  Scale: 1.000000
```
