"""Single-axis laser aiming: pan servo + laser emitter (PRD sections 7.1, 3).

Camera and laser are co-mounted on one pan-axis bracket, so whatever is centered
in the frame is where the laser points. On a detection we nudge the servo to
center the target horizontally, then hold the laser on it during the dwell.

Backends (auto-selected at import):
  - Servo PWM:
      * QNX (Pi 5): the BSP `rpi_gpio` Python module's hardware PWM in servo
        (MODE_MS) on a PWM-capable pin (GPIO 12/18 ch1, 13/19 ch2).
      * Raspberry Pi OS: `lgpio` servo pulses.
      * stub: prints the commanded angle.
  - Laser (digital on/off): `gpio-rp1` on QNX, `lgpio` on Linux, stub elsewhere.

Callers use aim.center_on(target_cx, frame_w), aim.laser("ON"|"OFF"),
aim.reset(); they never touch the backend.
"""
from __future__ import annotations

import time

from . import config


def pan_angle_for_target(target_cx: float, frame_width: int,
                         current_angle: float, gain: float | None = None) -> float:
    """One proportional pan correction (PRD 7.1). Smaller gain = gentler."""
    g = config.SERVO_GAIN if gain is None else gain
    error_px = target_cx - (frame_width / 2.0)
    return current_angle - (error_px * g)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _angle_to_duty(angle: float) -> float:
    """Map angle -> PWM duty cycle percent for the configured pulse range."""
    period_ms = 1000.0 / config.SERVO_FREQ_HZ
    span = config.SERVO_MAX_ANGLE - config.SERVO_MIN_ANGLE
    frac = 0.0 if span == 0 else (angle - config.SERVO_MIN_ANGLE) / span
    pulse_ms = config.SERVO_MIN_PULSE_MS + frac * (
        config.SERVO_MAX_PULSE_MS - config.SERVO_MIN_PULSE_MS
    )
    return (pulse_ms / period_ms) * 100.0


# --- servo backends -------------------------------------------------------
class _StubServo:
    name = "stub"

    def set_angle(self, angle: float) -> None:
        print(f"[SERVO:stub] angle={angle:.1f}")

    def cleanup(self) -> None:
        pass


class _QnxRpiGpioServo:
    """QNX hardware PWM via the BSP `rpi_gpio` module (servo MODE_MS)."""

    name = "qnx-rpi_gpio"

    def __init__(self):
        try:
            import rpi_gpio as GPIO  # type: ignore
        except Exception:
            from rpi_gpio import GPIO  # type: ignore

        self._GPIO = GPIO
        pin = config.SERVO_PWM_PIN
        # Best-effort: put the pin in its PWM alternate function first.
        self._set_alt_function(pin)
        mode = getattr(GPIO.PWM, "MODE_MS", None)
        if mode is not None:
            self._pwm = GPIO.PWM(pin, config.SERVO_FREQ_HZ, mode)
        else:
            self._pwm = GPIO.PWM(pin, config.SERVO_FREQ_HZ)
        self._pwm.start(_angle_to_duty(config.SERVO_CENTER_ANGLE))

    def _set_alt_function(self, pin: int) -> None:
        import shutil
        import subprocess

        if not shutil.which("gpio-rp1"):
            return
        alt = {12: "a0", 13: "a0", 18: "a3", 19: "a3"}.get(pin)
        if alt:
            subprocess.run(["gpio-rp1", "set", str(pin), alt],
                           check=False, capture_output=True)

    def set_angle(self, angle: float) -> None:
        self._pwm.ChangeDutyCycle(_angle_to_duty(angle))

    def cleanup(self) -> None:
        try:
            self._pwm.stop()
        except Exception:
            pass


class _LgpioServo:
    """Raspberry Pi OS backend using lgpio servo pulses (microseconds)."""

    name = "lgpio"

    def __init__(self):
        import lgpio

        self._lg = lgpio
        self._h = lgpio.gpiochip_open(0)
        self._pin = config.SERVO_PWM_PIN
        self.set_angle(config.SERVO_CENTER_ANGLE)

    def _angle_to_us(self, angle: float) -> int:
        span = config.SERVO_MAX_ANGLE - config.SERVO_MIN_ANGLE
        frac = 0.0 if span == 0 else (angle - config.SERVO_MIN_ANGLE) / span
        pulse_ms = config.SERVO_MIN_PULSE_MS + frac * (
            config.SERVO_MAX_PULSE_MS - config.SERVO_MIN_PULSE_MS
        )
        return int(pulse_ms * 1000)

    def set_angle(self, angle: float) -> None:
        self._lg.tx_servo(self._h, self._pin, self._angle_to_us(angle),
                          config.SERVO_FREQ_HZ)

    def cleanup(self) -> None:
        try:
            self._lg.tx_servo(self._h, self._pin, 0)
            self._lg.gpiochip_close(self._h)
        except Exception:
            pass


# --- laser backends -------------------------------------------------------
class _StubLaser:
    name = "stub"

    def set(self, on: bool) -> None:
        print(f"[LASER:stub] {'ON' if on else 'OFF'}")

    def cleanup(self) -> None:
        pass


class _QnxGpioLaser:
    name = "qnx-gpio-rp1"

    def __init__(self):
        import subprocess

        self._subprocess = subprocess
        self._pin = config.LASER_PIN
        self._run(["set", str(self._pin), "op", "dl"])

    def _run(self, args):
        self._subprocess.run(["gpio-rp1", *args], check=False, capture_output=True)

    def set(self, on: bool) -> None:
        self._run(["set", str(self._pin), "dh" if on else "dl"])

    def cleanup(self) -> None:
        self.set(False)


class _LgpioLaser:
    name = "lgpio"

    def __init__(self):
        import lgpio

        self._lg = lgpio
        self._h = lgpio.gpiochip_open(0)
        self._pin = config.LASER_PIN
        lgpio.gpio_claim_output(self._h, self._pin, 0)

    def set(self, on: bool) -> None:
        self._lg.gpio_write(self._h, self._pin, 1 if on else 0)

    def cleanup(self) -> None:
        try:
            self.set(False)
            self._lg.gpiochip_close(self._h)
        except Exception:
            pass


def _select_servo():
    import os
    import shutil

    if not config.SERVO_ENABLED:
        print("[SERVO] disabled (ACRE_SERVO_ENABLED=0); using stub.")
        return _StubServo()

    is_qnx = getattr(os, "uname", lambda: None)() and os.uname().sysname == "QNX"
    if is_qnx or shutil.which("gpio-rp1"):
        try:
            return _QnxRpiGpioServo()
        except Exception as exc:
            print(f"[SERVO] QNX rpi_gpio backend unavailable ({exc}); trying others.")
    try:
        import lgpio  # noqa: F401

        return _LgpioServo()
    except Exception as exc:
        print(f"[SERVO] GPIO PWM unavailable ({exc}); using stub.")
        return _StubServo()


def _select_laser():
    import os
    import shutil

    is_qnx = getattr(os, "uname", lambda: None)() and os.uname().sysname == "QNX"
    if (is_qnx or shutil.which("gpio-rp1")) and shutil.which("gpio-rp1"):
        try:
            return _QnxGpioLaser()
        except Exception as exc:
            print(f"[LASER] QNX gpio-rp1 backend failed ({exc}); trying others.")
    try:
        import lgpio  # noqa: F401

        return _LgpioLaser()
    except Exception as exc:
        print(f"[LASER] GPIO backend unavailable ({exc}); using stub.")
        return _StubLaser()


class _AimState:
    def __init__(self):
        self.angle = config.SERVO_CENTER_ANGLE
        self.servo = _select_servo()
        self.laser_backend = _select_laser()


_state = _AimState()


def set_angle(angle: float) -> float:
    """Command an absolute pan angle (clamped). Returns the applied angle."""
    angle = _clamp(angle, config.SERVO_MIN_ANGLE, config.SERVO_MAX_ANGLE)
    _state.servo.set_angle(angle)
    _state.angle = angle
    return angle


def step_toward(target_cx: float, frame_width: int) -> tuple[float, float, bool]:
    """Apply one proportional correction. Returns (angle, error_px, locked)."""
    error_px = target_cx - (frame_width / 2.0)
    locked = abs(error_px) <= config.AIM_TOLERANCE_PX
    if not locked:
        set_angle(pan_angle_for_target(target_cx, frame_width, _state.angle))
    return _state.angle, error_px, locked


def center_on(target_cx: float, frame_width: int,
              get_target_cx=None) -> bool:
    """Pan to center the target horizontally. Returns whether it locked.

    Because the camera and laser share the pan axis, every correction physically
    moves the camera too, so each step needs a fresh measurement to converge
    (PRD 7.1). Pass `get_target_cx` (called after each move, returning the new
    centroid or None) for a true closed loop within one dwell. Without it, we
    apply a single proportional correction and let successive dwells converge —
    repeating with a stale centroid would just overshoot.
    """
    locked = False
    for _ in range(config.AIM_MAX_STEPS):
        _, _, locked = step_toward(target_cx, frame_width)
        if locked or get_target_cx is None:
            break
        time.sleep(0.05)
        nxt = get_target_cx()
        if nxt is None:
            break
        target_cx = nxt
    return locked


def laser(state: str) -> None:
    _state.laser_backend.set(str(state).upper() == "ON")


def reset() -> None:
    laser("OFF")
    set_angle(config.SERVO_CENTER_ANGLE)


def cleanup() -> None:
    try:
        _state.laser_backend.cleanup()
    finally:
        _state.servo.cleanup()


def backend_name() -> str:
    return f"servo={_state.servo.name} laser={_state.laser_backend.name}"
