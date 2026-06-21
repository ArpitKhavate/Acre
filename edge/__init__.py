"""Acre edge package — all on-device, offline-first scanning logic.

Modules:
  config         device configuration (env-overridable)
  capture        Pi Camera Module 3 capture (with fallbacks)
  aruco_zones    ArUco marker -> zone_id resolution (GPS-free localization)
  detect         ONNX detector + disease/pest classifiers (local inference)
  health_score   per-plant 0-100 score -> LED color decision
  led            Pi GPIO red/green LED + buzzer (spray-substitute signal)
  rtc            authoritative RTC timestamp (DS1302) with fallback
  local_db       offline-first SQLite logging
  sync_agent     opportunistic, idempotent push to the cloud backend
  main           the scan loop tying it all together
"""

__version__ = "0.1.0"
