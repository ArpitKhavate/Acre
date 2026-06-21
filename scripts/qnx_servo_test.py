#!/usr/bin/env python3
"""Pan-servo sweep + laser blink test, via edge/aim.py.

Exercises whichever servo/laser backend resolves on this machine (QNX rpi_gpio
PWM, Linux lgpio, or a printing stub), so it is safe to run anywhere.

    python3 scripts/qnx_servo_test.py

SAFETY: never aim the laser at anyone's eyes.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge import aim, config  # noqa: E402


def main() -> None:
    print("aim backend:", aim.backend_name())
    sweep = [
        config.SERVO_CENTER_ANGLE,
        config.SERVO_MIN_ANGLE,
        config.SERVO_CENTER_ANGLE,
        config.SERVO_MAX_ANGLE,
        config.SERVO_CENTER_ANGLE,
    ]
    for angle in sweep:
        applied = aim.set_angle(angle)
        print(f"  servo -> {applied:.1f} deg")
        time.sleep(1.0)

    print("laser ON (1s)")
    aim.laser("ON")
    time.sleep(1.0)
    aim.laser("OFF")
    print("laser OFF")

    aim.cleanup()
    print("Done. If the servo swept and the laser blinked, wiring is correct.")


if __name__ == "__main__":
    main()
