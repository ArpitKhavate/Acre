"""Pi GPIO red/green status LED + buzzer — the spray-substitute signal.

GREEN = plant healthy (beats the health threshold).
RED   = plant needs treatment (disease/pest, or below threshold).
BLUE  = syncing (optional).

Backend is auto-selected at import:
  - `lgpio`   on a Raspberry Pi running Linux,
  - QNX GPIO  on the device (hook provided, fill in BSP specifics),
  - a no-op   stub on a dev laptop so the whole pipeline runs anywhere.

The rest of the codebase only calls led.set("RED") / led.set("GREEN") and
led.beep(); it never touches the backend directly.
"""
from __future__ import annotations

from . import config

_VALID = {"RED", "GREEN", "BLUE", "OFF"}


class _StubBackend:
    """Prints instead of toggling pins. Used on laptops / when GPIO is absent."""

    name = "stub"

    def set(self, color: str) -> None:
        print(f"[LED:stub] {color}")

    def beep(self, ms: int) -> None:
        print(f"[BUZZ:stub] {ms}ms")

    def cleanup(self) -> None:
        pass


class _QnxGpioBackend:
    """QNX (Raspberry Pi 5) backend using the BSP's `gpio-rp1` utility.

    Docs: gpio-rp1 set <pin> op   -> output
          gpio-rp1 set <pin> dh   -> drive high (on)
          gpio-rp1 set <pin> dl   -> drive low  (off)
    Pins are BCM numbers, which is exactly what gpio-rp1 expects.
    """

    name = "qnx-gpio-rp1"

    def __init__(self):
        import subprocess

        self._subprocess = subprocess
        self._pins = {
            "RED": config.LED_RED_PIN,
            "GREEN": config.LED_GREEN_PIN,
            "BLUE": config.LED_BLUE_PIN,
        }
        # Configure every pin as an output, initially off.
        for pin in list(self._pins.values()) + [config.BUZZER_PIN]:
            self._run(["set", str(pin), "op", "dl"])

    def _run(self, args):
        self._subprocess.run(["gpio-rp1", *args], check=False,
                             capture_output=True)

    def set(self, color: str) -> None:
        for name, pin in self._pins.items():
            self._run(["set", str(pin), "dh" if name == color else "dl"])

    def beep(self, ms: int) -> None:
        import time

        self._run(["set", str(config.BUZZER_PIN), "dh"])
        time.sleep(ms / 1000.0)
        self._run(["set", str(config.BUZZER_PIN), "dl"])

    def cleanup(self) -> None:
        self.set("OFF")


class _LgpioBackend:
    """Raspberry Pi (Linux) backend using the lgpio library."""

    name = "lgpio"

    def __init__(self):
        import lgpio

        self._lg = lgpio
        self._h = lgpio.gpiochip_open(0)
        self._pins = {
            "RED": config.LED_RED_PIN,
            "GREEN": config.LED_GREEN_PIN,
            "BLUE": config.LED_BLUE_PIN,
        }
        for pin in self._pins.values():
            lgpio.gpio_claim_output(self._h, pin, 0)
        lgpio.gpio_claim_output(self._h, config.BUZZER_PIN, 0)

    def set(self, color: str) -> None:
        for name, pin in self._pins.items():
            self._lg.gpio_write(self._h, pin, 1 if name == color else 0)

    def beep(self, ms: int) -> None:
        import time

        self._lg.gpio_write(self._h, config.BUZZER_PIN, 1)
        time.sleep(ms / 1000.0)
        self._lg.gpio_write(self._h, config.BUZZER_PIN, 0)

    def cleanup(self) -> None:
        self.set("OFF")
        self._lg.gpiochip_close(self._h)


def _select_backend():
    import os
    import shutil

    # QNX (Pi 5): drive the LED through the BSP's gpio-rp1 utility.
    is_qnx = getattr(os, "uname", lambda: None)() and os.uname().sysname == "QNX"
    if (is_qnx or shutil.which("gpio-rp1")) and shutil.which("gpio-rp1"):
        try:
            return _QnxGpioBackend()
        except Exception as exc:
            print(f"[LED] QNX gpio-rp1 backend failed ({exc}); trying others.")

    # Raspberry Pi OS (Linux): lgpio library.
    try:
        import lgpio  # noqa: F401

        return _LgpioBackend()
    except Exception as exc:  # ImportError on laptop, RuntimeError if no chip
        print(f"[LED] GPIO backend unavailable ({exc}); using stub.")
        return _StubBackend()


_backend = _select_backend()


def set(color: str) -> None:
    color = color.upper()
    if color not in _VALID:
        raise ValueError(f"color must be one of {_VALID}, got {color!r}")
    _backend.set(color)


def beep(ms: int = 150) -> None:
    _backend.beep(ms)


def signal_for_score(health_score: float, threshold: float | None = None,
                     buzz_on_red: bool = True) -> str:
    """Drive the LED from a health score. Returns the LED state chosen."""
    thr = config.HEALTH_THRESHOLD if threshold is None else threshold
    state = "GREEN" if health_score >= thr else "RED"
    set(state)
    if state == "RED" and buzz_on_red:
        beep()
    return state


def cleanup() -> None:
    _backend.cleanup()


def backend_name() -> str:
    return _backend.name
