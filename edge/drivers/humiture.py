"""DHT11 single-wire humiture driver (PRD section 6).

The DHT11 has no I2C; it uses a timing-critical one-wire protocol (the host
pulls the line low, then the sensor replies with 40 bits encoded as variable
HIGH-pulse widths). This is a best-effort bit-bang in Python and is inherently
marginal on QNX, which gives the Python layer no hard real-time guarantees — so
reads can fail and are retried, and the caller falls back to "no reading" when
they do. Prefer an I2C humiture part (AHT20/DHT20/SHT3x) if reliability matters.

Backends, selected at open time:
  - QNX (Pi 5): the BSP `rpi_gpio` module (RPi.GPIO-compatible API).
  - Raspberry Pi OS: `lgpio`.
If neither is importable (e.g. a laptop), `open_sensor` raises and the caller
(`edge/sensors.py`) drops back to synthetic readings.
"""
from __future__ import annotations

import time

# A data-bit HIGH pulse longer than this is a '1' (DHT11: '0' ~27us, '1' ~70us).
_BIT1_THRESHOLD_NS = 50_000
# How long to listen for the full 40-bit frame (a frame is ~4-5 ms).
_FRAME_WINDOW_NS = 10_000_000


def _decode(transitions) -> tuple[float, float] | None:
    """Decode (level, timestamp) transitions into (temperature_c, humidity_pct)."""
    highs = []
    for i in range(1, len(transitions)):
        t_prev, lvl_prev = transitions[i - 1]
        t_cur, lvl_cur = transitions[i]
        if lvl_prev == 1 and lvl_cur == 0:      # a HIGH pulse just ended
            highs.append(t_cur - t_prev)
    if len(highs) < 41:                          # 1 response pulse + 40 data bits
        return None
    bits = highs[-40:]                           # last 40 highs are the data bits
    value = 0
    for dur in bits:
        value = (value << 1) | (1 if dur > _BIT1_THRESHOLD_NS else 0)
    b = [(value >> (8 * i)) & 0xFF for i in (4, 3, 2, 1, 0)]
    if ((b[0] + b[1] + b[2] + b[3]) & 0xFF) != b[4]:
        return None                              # checksum mismatch
    humidity = float(b[0])                       # DHT11: integer humidity in b[0]
    temperature = float(b[2])                    # integer temperature in b[2]
    return temperature, humidity


class _RpiGpioOps:
    """QNX `rpi_gpio` (RPi.GPIO-compatible) one-wire bus operations."""

    name = "rpi_gpio"

    def __init__(self, pin: int):
        try:
            import rpi_gpio as GPIO  # type: ignore
        except Exception:
            from rpi_gpio import GPIO  # type: ignore
        self._GPIO = GPIO
        self._pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)

    def drive_low(self) -> None:
        g = self._GPIO
        g.setup(self._pin, g.OUT)
        g.output(self._pin, g.LOW)

    def release_input(self) -> None:
        self._GPIO.setup(self._pin, self._GPIO.IN)

    def read(self) -> int:
        return 1 if self._GPIO.input(self._pin) else 0

    def close(self) -> None:
        pass


class _LgpioOps:
    """Raspberry Pi OS `lgpio` one-wire bus operations."""

    name = "lgpio"

    def __init__(self, pin: int):
        import lgpio

        self._lg = lgpio
        self._h = lgpio.gpiochip_open(0)
        self._pin = pin
        lgpio.gpio_claim_input(self._h, pin)

    def drive_low(self) -> None:
        self._lg.gpio_claim_output(self._h, self._pin, 0)

    def release_input(self) -> None:
        try:
            self._lg.gpio_claim_input(self._h, self._pin)
        except Exception:
            pass

    def read(self) -> int:
        return 1 if self._lg.gpio_read(self._h, self._pin) else 0

    def close(self) -> None:
        try:
            self._lg.gpiochip_close(self._h)
        except Exception:
            pass


class HumitureSensor:
    """A DHT11 on a GPIO pin. read() returns (temp_c, humidity) or None.

    Reads are throttled to `min_interval` seconds and the last good value is
    cached, both to respect the DHT11's ~1 Hz limit and to keep the scan loop
    from blocking on a sensor that is allowed to be flaky.
    """

    def __init__(self, ops, min_interval: float = 2.0):
        self._ops = ops
        self._min_interval = min_interval
        self._last_attempt = 0.0
        self._cached: tuple[float, float] | None = None

    @property
    def backend(self) -> str:
        return self._ops.name

    def _read_once(self) -> tuple[float, float] | None:
        ops = self._ops
        ops.drive_low()
        time.sleep(0.020)                        # >=18 ms start signal
        ops.release_input()                      # module's pull-up takes the line
        transitions = []
        last = ops.read()
        now = time.perf_counter_ns
        end = now() + _FRAME_WINDOW_NS
        while now() < end:
            level = ops.read()
            if level != last:
                transitions.append((now(), level))
                last = level
        return _decode(transitions)

    def read(self) -> tuple[float, float] | None:
        elapsed = time.monotonic() - self._last_attempt
        if elapsed < self._min_interval and self._cached is not None:
            return self._cached
        self._last_attempt = time.monotonic()
        for _ in range(3):
            try:
                result = self._read_once()
            except Exception:
                result = None
            if result is not None:
                self._cached = result
                return result
            time.sleep(0.05)
        return self._cached                      # may be None on a fresh start

    def close(self) -> None:
        self._ops.close()


def open_sensor(pin: int, min_interval: float = 2.0) -> HumitureSensor:
    """Open a DHT11 on `pin`, choosing the QNX or Linux backend. Raises if
    neither GPIO backend is importable (the caller then uses synthetic data)."""
    try:
        ops = _RpiGpioOps(pin)
    except Exception:
        ops = _LgpioOps(pin)                     # ImportError here propagates up
    return HumitureSensor(ops, min_interval)
