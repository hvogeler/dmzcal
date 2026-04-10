# Raspberry Pi Touch Display 2 — Touch Calibration Fix

**Device:** Raspberry Pi 5 + official 7" Touch Display 2 (ILI9881C panel, Goodix touch controller)
**OS:** Raspberry Pi OS Bookworm (labwc Wayland compositor)
**Problem:** After upgrading labwc to 0.8.4, touch input is misaligned when the display is rotated to landscape via kanshi `transform 270`.

## Root Cause

labwc 0.8.4 (+ libwlroots 0.18.2-3+rpt4) does not correctly apply touch coordinate transformation for rotated DSI displays. The touch axes remain in the native portrait coordinate space (720×1280) while the display is rendered in landscape.

## Fix

Add the following line to `/boot/firmware/config.txt` in the `[all]` section:

```
dtoverlay=vc4-kms-dsi-ili9881-7inch,swapxy,invx
```

This instructs the kernel-level Goodix touch driver to swap and invert axes, compensating for the landscape rotation.

## Required Configuration Files

### /boot/firmware/config.txt

Ensure these settings are present:

```
display_auto_detect=1
```

And in the `[all]` section at the end:

```
[all]
dtoverlay=vc4-kms-dsi-ili9881-7inch,swapxy,invx
```

### ~/.config/kanshi/config (user: ubuntu)

```
profile {
		output DSI-2 enable mode 720x1280@60.038 position 0,0 transform 270
}
```

### ~/.config/labwc/rc.xml (user: ubuntu)

```xml
<?xml version="1.0"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
<touch deviceName="11-005d Goodix Capacitive TouchScreen" mapToOutput="DSI-2" mouseEmulation="yes"/>
<libinput><device category="default"><pointerSpeed>0.000000</pointerSpeed><leftHanded>no</leftHanded></device></libinput>
<mouse><doubleClickTime>400</doubleClickTime></mouse>
<keyboard><repeatRate>25</repeatRate><repeatDelay>600</repeatDelay></keyboard>
</openbox_config>
```

### Cleanup

Ensure no leftover udev calibration rules exist:

```bash
ls /etc/udev/rules.d/*touch* /etc/udev/rules.d/*calib* 2>/dev/null
# Should return nothing
```

Ensure `/boot/firmware/cmdline.txt` has **no** `video=DSI-...` parameter.

## Optional: Pin labwc Version

To prevent future upgrades from breaking touch again:

```bash
sudo apt-mark hold labwc
# To unhold later:
sudo apt-mark unhold labwc
```
