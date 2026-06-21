"""I2C 1602 LCD — shows the live health score (PRD section 6, on-device display).

A 16x2 HD44780 LCD driven over a PCF8574 I2C backpack. The display is the
"fully offline" status readout: it shows the current zone, the 0-100 health
score, and the finding, with no laptop attached.

Backend is auto-selected at import:
  - QNX (Pi 5): writes bytes via the BSP's `isendrecv` utility on /dev/i2c1,
    since QNX has no read()/write() for I2C (devctl/isendrecv only).
  - Raspberry Pi OS (Linux): the `smbus2` library.
  - a no-op stub on a dev laptop so the pipeline runs anywhere.

The rest of the codebase only calls lcd.show_score(...) / lcd.show(...); it
never touches the backend. Writes are de-duplicated so we only hit the slow I2C
path when the displayed text actually changes.
"""
from __future__ import annotations

import time

from . import config

# PCF8574 -> HD44780 bit mapping for the common "LCD1602 I2C" backpack.
_RS = 0x01          # register select: 0 = command, 1 = data
_EN = 0x04          # enable strobe
_BACKLIGHT = 0x08   # backlight on
_LCD_WIDTH = 16


class _StubWriter:
    name = "stub"

    def __init__(self):
        self._last = ("", "")

    def write_byte(self, value: int) -> None:  # pragma: no cover - trivial
        pass

    def show_text(self, line1: str, line2: str) -> None:
        if (line1, line2) != self._last:
            self._last = (line1, line2)
            print(f"[LCD:stub] | {line1:<16} | {line2:<16} |")

    def cleanup(self) -> None:
        pass


class _Hd44780ViaBytes:
    """HD44780 4-bit protocol on top of a single-byte I2C writer.

    Subclasses implement `_raw(value)` to push one byte to the PCF8574.
    """

    name = "base"

    def __init__(self):
        self._last = (None, None)
        self._init_display()

    # --- backend hook -----------------------------------------------------
    def _raw(self, value: int) -> None:
        raise NotImplementedError

    # --- HD44780 plumbing -------------------------------------------------
    def _strobe(self, data: int) -> None:
        self._raw(data | _EN | _BACKLIGHT)
        time.sleep(0.0005)
        self._raw((data & ~_EN) | _BACKLIGHT)
        time.sleep(0.0001)

    def _write4(self, nibble: int) -> None:
        self._raw(nibble | _BACKLIGHT)
        self._strobe(nibble)

    def _send(self, value: int, mode: int) -> None:
        self._write4((value & 0xF0) | mode)
        self._write4(((value << 4) & 0xF0) | mode)

    def _command(self, value: int) -> None:
        self._send(value, 0)

    def _data(self, value: int) -> None:
        self._send(value, _RS)

    def _init_display(self) -> None:
        # 4-bit init sequence per the HD44780 datasheet.
        time.sleep(0.05)
        for _ in range(3):
            self._write4(0x30)
            time.sleep(0.005)
        self._write4(0x20)            # set 4-bit mode
        self._command(0x28)           # 4-bit, 2 lines, 5x8 font
        self._command(0x0C)           # display on, cursor off
        self._command(0x06)           # entry mode: increment
        self._command(0x01)           # clear
        time.sleep(0.002)

    def show_text(self, line1: str, line2: str) -> None:
        if (line1, line2) == self._last:
            return
        self._last = (line1, line2)
        for addr, text in ((0x80, line1), (0xC0, line2)):
            self._command(addr)
            for ch in text.ljust(_LCD_WIDTH)[:_LCD_WIDTH]:
                self._data(ord(ch))

    def cleanup(self) -> None:
        try:
            self._command(0x01)       # clear
            self._raw(0x00)           # backlight off
        except Exception:
            pass


class _QnxIsendrecvWriter(_Hd44780ViaBytes):
    """QNX backend: each byte is one `isendrecv` send on /dev/i2c1."""

    name = "qnx-isendrecv"

    def __init__(self):
        import subprocess

        self._subprocess = subprocess
        self._addr = config.LCD_I2C_ADDR
        self._bus = config.LCD_I2C_BUS
        super().__init__()

    def _raw(self, value: int) -> None:
        self._subprocess.run(
            ["isendrecv", "-a", hex(self._addr), "-n", self._bus, hex(value & 0xFF)],
            check=False, capture_output=True,
        )


class _Smbus2Writer(_Hd44780ViaBytes):
    """Raspberry Pi OS backend using smbus2."""

    name = "smbus2"

    def __init__(self):
        from smbus2 import SMBus

        self._addr = config.LCD_I2C_ADDR
        bus = config.LCD_I2C_BUS
        # Accept either an int bus number or a "/dev/i2c-N" path.
        if isinstance(bus, str) and not bus.lstrip("-").isdigit():
            import re

            m = re.search(r"(\d+)", bus)
            bus = int(m.group(1)) if m else 1
        self._bus = SMBus(int(bus))
        super().__init__()

    def _raw(self, value: int) -> None:
        self._bus.write_byte(self._addr, value & 0xFF)

    def cleanup(self) -> None:
        super().cleanup()
        try:
            self._bus.close()
        except Exception:
            pass


def _select_backend():
    if not config.LCD_ENABLED:
        return _StubWriter()

    import os
    import shutil

    is_qnx = getattr(os, "uname", lambda: None)() and os.uname().sysname == "QNX"
    if (is_qnx or shutil.which("isendrecv")) and shutil.which("isendrecv"):
        try:
            return _QnxIsendrecvWriter()
        except Exception as exc:
            print(f"[LCD] QNX isendrecv backend failed ({exc}); trying others.")

    try:
        import smbus2  # noqa: F401

        return _Smbus2Writer()
    except Exception as exc:
        print(f"[LCD] I2C backend unavailable ({exc}); using stub.")
        return _StubWriter()


_backend = _select_backend()


def show(line1: str = "", line2: str = "") -> None:
    """Display two lines (truncated/padded to 16 chars each)."""
    _backend.show_text(str(line1)[:_LCD_WIDTH], str(line2)[:_LCD_WIDTH])


def show_score(zone: str, score: float, finding: str) -> None:
    """Top line: zone + health score /100. Bottom line: the finding."""
    line1 = f"{str(zone)[:4]:<4} HEALTH {int(round(score)):>3}"
    show(line1, finding)


def cleanup() -> None:
    _backend.cleanup()


def backend_name() -> str:
    return _backend.name
