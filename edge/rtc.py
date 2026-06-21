"""Timestamp source for logged events.

The DS1302 hardware RTC is intentionally NOT used in this build. Instead we use
the board's system clock. On QNX, set the clock once at setup from an
NTP-synced machine (or `date`/`rtc` at boot) so `captured_at` is sensible:

    # on the QNX target, e.g.
    date -s "2026-06-21 01:30:00"

Every timestamp is UTC ISO-8601.
"""
from __future__ import annotations

import datetime as _dt


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def source() -> str:
    return "system"
