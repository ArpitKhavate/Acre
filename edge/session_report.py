"""Roll up an in-memory scan session into a farm health report + AI summary.

Used by the webcam demo (press F) and later by the QNX → laptop sync path.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from . import treatments as trt


def _ai_summary(period_data: dict) -> str:
    try:
        from cloud.app.ai_summary import generate_summary
        return generate_summary(period_data)
    except Exception:
        return _fallback_summary(period_data)


def _fallback_summary(data: dict) -> str:
    score = data.get("farm_health", "n/a")
    pest = data.get("top_pest", "none")
    chem = data.get("top_pesticide", "none")
    plants = data.get("plant_count", 0)
    weeds = data.get("weed_count", 0)
    parts = [
        f"After {data.get('scan_count', 0)} scans across {plants} plants, "
        f"farm health averages {score}/100.",
    ]
    if weeds:
        parts.append(f"Weeds were flagged in {weeds} scan(s) — spot-treat those rows first.")
    if pest and pest != "None detected":
        parts.append(f"The most common pest signal was {pest}.")
    if chem and chem not in ("None needed", "None"):
        parts.append(f"Priority treatment: {chem}.")
    elif score >= 70:
        parts.append("No urgent pesticide applications are indicated.")
    parts.append("Re-scan treated areas in 48–72 hours to confirm recovery.")
    return " ".join(parts)


def scan_from_result(score, result) -> dict:
    """Serialize one pipeline result for session storage."""
    pest = result.pest_class if result.pest_class else None
    pesticide = score.pesticide
    if pest and not pesticide:
        pesticide = trt.pesticide_for(pest)
    return {
        "type": score.type,
        "class_name": score.class_name,
        "health_score": score.score,
        "led_state": score.led_state,
        "pest_class": pest,
        "pest_conf": round(float(result.pest_conf), 3) if pest else 0.0,
        "disease_class": result.disease_class,
        "is_healthy": result.is_healthy,
        "primary_pesticide": pesticide,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def build_session_report(scans: list[dict]) -> dict[str, Any]:
    if not scans:
        raise ValueError("need at least one scan to build a report")

    scores = [s["health_score"] for s in scans if s.get("health_score") is not None]
    farm_health = round(sum(scores) / len(scores), 1) if scores else 0.0

    plant_count = sum(1 for s in scans if s.get("type") != "weed")
    weed_count = sum(1 for s in scans if s.get("type") == "weed")
    disease_count = sum(1 for s in scans if s.get("type") == "disease")
    pest_count = sum(1 for s in scans if s.get("pest_class"))

    pests = [s["pest_class"] for s in scans if s.get("pest_class")]
    top_pest = pests and Counter(pests).most_common(1)[0][0]
    top_pest_n = Counter(pests).most_common(1)[0][1] if pests else 0

    chem_list: list[str] = []
    for s in scans:
        if s.get("type") == "healthy":
            continue
        chem = s.get("primary_pesticide") or trt.primary_pesticide(
            s.get("type", ""), s.get("class_name", "")
        )
        if chem and chem not in ("None", "None needed"):
            chem_list.append(chem)
    top_pesticide = Counter(chem_list).most_common(1)[0][0] if chem_list else "None needed"

    period_data = {
        "farm_score": farm_health,
        "scan_count": len(scans),
        "plant_count": plant_count,
        "weed_count": weed_count,
        "disease_count": disease_count,
        "pest_signals": pest_count,
        "top_pest": top_pest or "None detected",
        "treatments_needed": list(dict.fromkeys(chem_list))[:5],
        "worst_zones": [],  # single-handheld session — no zones yet
    }

    status = "healthy" if farm_health >= 70 else "attention" if farm_health >= 50 else "critical"

    return {
        "ready": True,
        "farm_health": farm_health,
        "status": status,
        "scan_count": len(scans),
        "plant_count": plant_count,
        "weed_count": weed_count,
        "disease_count": disease_count,
        "pest_signals": pest_count,
        "top_pest": top_pest or "None detected",
        "top_pest_count": top_pest_n,
        "top_pesticide": top_pesticide,
        "treatments_needed": period_data["treatments_needed"],
        "ai_summary": _ai_summary({**period_data, "farm_health": farm_health,
                                   "top_pesticide": top_pesticide}),
        "findings": scans[-12:],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
