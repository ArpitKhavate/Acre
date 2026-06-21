"""One-shot hardware/backends self-check: ``python3 -m edge.hwcheck``.

Initializes every backend and reports which concrete driver each resolved to
(real / stub / synthetic), grabs one camera frame, and writes a line to the
LCD. It does NOT fire the laser. Run it on a laptop (expect all stub/synthetic,
no crash) and on the Pi 5 / QNX (expect the real backends).
"""
from __future__ import annotations

from . import config


def main() -> None:
    print(f"[hwcheck] device={config.DEVICE_ID}")
    rows: list[tuple[str, str]] = []

    from . import led
    rows.append(("led", led.backend_name()))

    from . import aim
    rows.append(("aim", aim.backend_name()))

    from . import lcd
    try:
        lcd.show("ACRE hwcheck", "backends ok")
    except Exception as exc:
        rows.append(("lcd_write", f"ERR {exc}"))
    rows.append(("lcd", lcd.backend_name()))

    from . import capture
    cam = capture.Camera()
    rows.append(("camera", cam.backend))
    try:
        frame = cam.read()
        rows.append(("camera_frame", str(frame.shape)))
    except Exception as exc:
        rows.append(("camera_frame", f"ERR {exc}"))
    cam.close()

    from . import sensors
    sensor_unit = sensors.Sensors()
    rows.append(("sensors", sensor_unit.backend))
    reading = sensor_unit.read()
    rows.append(("sensor_read",
                 f"T={reading.temperature_c} H={reading.humidity_pct}"))

    from . import detect
    detector = detect.Detector()
    rows.append(("models", str(detector.backends())))

    print()
    for name, value in rows:
        print(f"  {name:<14} {value}")
    print()

    aim.cleanup()
    lcd.cleanup()
    led.cleanup()
    print("[hwcheck] done")


if __name__ == "__main__":
    main()
