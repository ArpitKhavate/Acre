"""Authoritative timestamp source (PRD section 6).

QNX has no guaranteed network time sync in the field, so the system clock can
drift or reset on power-down. The DS1302 RTC is set once via an NTP-synced
laptop at setup, then read for every `captured_at`.

If the RTC isn't wired (dev laptop), we fall back to the system clock but stamp
the source so it's auditable. Either way, callers get an ISO-8601 string.
"""
from __future__ import annotations

import datetime as _dt


class Clock:
    def __init__(self):
        self.source = "system"
        self._rtc = None
        self._init_rtc()

    def _init_rtc(self):
        # Hook for a DS1302 driver wired to Pi GPIO. Many DS1302 libs are
        # bit-banged over three GPIO lines; plug yours in here and set
        # self.source = "rtc". Left unimplemented so dev boxes use the system
        # clock cleanly rather than crashing.
        try:
            # from .drivers.ds1302 import DS1302
            # self._rtc = DS1302(clk=..., dat=..., rst=...)
            # self.source = "rtc"
            raise ImportError
        except Exception:
            self.source = "system"

    def now_iso(self) -> str:
        if self._rtc is not None:
            return self._rtc.read_datetime().isoformat()
        return _dt.datetime.now(_dt.timezone.utc).isoformat()


_clock = Clock()


def now_iso() -> str:
    return _clock.now_iso()


def source() -> str:
    return _clock.source
