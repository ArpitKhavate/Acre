"""On-device field report (PRD sections 9-10), generated fully offline on QNX.

Reads the local SQLite log the scan loop writes and rolls it up into a plain
report: which zones have low health, in what area of the plot, what pests /
weeds / diseases were found, and which pesticide each needs (from the local
UC IPM treatments table). No numpy, no network, no cloud — just the standard
library — so it runs on the QNX board even before the vision stack is ported.

    python3 -m edge.report                 # print one report
    python3 -m edge.report --watch         # refresh every 30s (the periodic mode)
    python3 -m edge.report --watch --interval 20 --lcd
    python3 -m edge.report --window 6      # only the last 6 hours

Each run also writes edge/reports/latest.txt and latest.json.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config, local_db


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _area_label(map_x: float, map_y: float) -> str:
    vert = "back" if map_y < 0.4 else "front" if map_y > 0.6 else "mid"
    horiz = "left" if map_x < 0.4 else "right" if map_x > 0.6 else "center"
    return f"{vert}-{horiz}"


def build_report(conn: sqlite3.Connection, window_hours: float | None = None,
                 threshold: float | None = None) -> dict:
    window_hours = config.REPORT_WINDOW_HOURS if window_hours is None else window_hours
    threshold = config.HEALTH_THRESHOLD if threshold is None else threshold

    zones_data = _load_json(config.ZONES_CONFIG)
    treatments = _load_json(config.TREATMENTS_CONFIG).get("treatments", {})
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()

    conn.row_factory = sqlite3.Row
    zones_out: list[dict] = []
    scored: list[float] = []

    for z in zones_data["zones"]:
        zid = z["zone_id"]
        rows = conn.execute(
            "SELECT * FROM detections WHERE zone_id = ? AND captured_at >= ? "
            "ORDER BY captured_at DESC",
            (zid, cutoff),
        ).fetchall()
        area = _area_label(z.get("map_x", 0.5), z.get("map_y", 0.5))
        crop = z.get("crop_type")

        if not rows:
            zones_out.append({"zone_id": zid, "crop": crop, "area": area,
                              "scans": 0, "health": None, "status": "no-data",
                              "findings": []})
            continue

        scores = [r["health_score"] for r in rows if r["health_score"] is not None]
        avg = round(sum(scores) / len(scores), 1) if scores else 100.0
        scored.append(avg)

        grouped: dict[tuple, dict] = {}
        for r in rows:
            if r["type"] == "healthy":
                continue
            key = (r["type"], r["class_name"])
            f = grouped.setdefault(key, {"type": r["type"],
                                         "class_name": r["class_name"],
                                         "count": 0, "max_conf": 0.0})
            f["count"] += 1
            f["max_conf"] = max(f["max_conf"], r["confidence"] or 0.0)

        findings = []
        for f in grouped.values():
            f["max_conf"] = round(f["max_conf"], 2)
            f["treatment"] = treatments.get(f["class_name"])
            findings.append(f)
        findings.sort(key=lambda f: -f["max_conf"])

        status = "low" if (avg < threshold or findings) else "healthy"
        zones_out.append({"zone_id": zid, "crop": crop, "area": area,
                          "scans": len(rows), "health": avg, "status": status,
                          "findings": findings})

    farm_score = round(sum(scored) / len(scored), 1) if scored else None
    attention = sorted([z for z in zones_out if z["status"] == "low"],
                       key=lambda z: z["health"] if z["health"] is not None else 999)

    treatments_needed = []
    for z in attention:
        for f in z["findings"]:
            t = f.get("treatment")
            if t and t["pesticide"] not in [x["pesticide"] for x in treatments_needed]:
                treatments_needed.append({"pesticide": t["pesticide"],
                                          "for": f["class_name"], "zone": z["zone_id"]})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_hours": window_hours,
        "farm_id": zones_data.get("farm_id", config.FARM_ID),
        "farm_score": farm_score,
        "zones": zones_out,
        "attention": [z["zone_id"] for z in attention],
        "treatments_needed": treatments_needed,
    }


def render_text(report: dict) -> str:
    lines = []
    lines.append("=" * 52)
    lines.append("              ACRE FIELD REPORT")
    lines.append("=" * 52)
    score = report["farm_score"]
    lines.append(f"Generated: {report['generated_at']}   (last {report['window_hours']:g}h)")
    lines.append(f"Farm: {report['farm_id']}     "
                 f"Farm health: {score if score is not None else 'n/a'}/100")
    lines.append("")

    attention = [z for z in report["zones"] if z["status"] == "low"]
    healthy = [z for z in report["zones"] if z["status"] == "healthy"]
    nodata = [z for z in report["zones"] if z["status"] == "no-data"]

    lines.append(f"ZONES NEEDING ATTENTION ({len(attention)})")
    if not attention:
        lines.append("  none")
    for z in attention:
        lines.append(f"  {z['zone_id']}  ({z['crop']}, {z['area']})  "
                     f"health {z['health']}/100  LOW")
        if not z["findings"]:
            lines.append("    - low health score (no specific finding)")
        for f in z["findings"]:
            lines.append(f"    - {f['type']}: {f['class_name']}  "
                         f"x{f['count']}  conf {f['max_conf']}")
            t = f.get("treatment")
            if t:
                lines.append(f"        -> {t['pesticide']}   (organic: {t['organic']})")
                lines.append(f"           {t['notes']}")
            else:
                lines.append("        -> no treatment on file")
    lines.append("")

    lines.append(f"HEALTHY ZONES ({len(healthy)})")
    for z in healthy:
        lines.append(f"  {z['zone_id']}  ({z['crop']}, {z['area']})  health {z['health']}/100")
    if nodata:
        lines.append("")
        lines.append(f"NO DATA THIS WINDOW ({len(nodata)})")
        lines.append("  " + ", ".join(z["zone_id"] for z in nodata))

    lines.append("")
    lines.append("SUMMARY")
    if attention:
        worst = attention[0]
        lines.append(f"  {len(attention)} of {len(report['zones'])} zones need attention. "
                     f"Worst: {worst['zone_id']} ({worst['health']}/100).")
    else:
        lines.append("  All scanned zones are healthy.")
    if report["treatments_needed"]:
        tn = ", ".join(f"{t['pesticide']} ({t['zone']})" for t in report["treatments_needed"])
        lines.append(f"  Treatments needed: {tn}")
    lines.append("=" * 52)
    return "\n".join(lines)


def render_lcd(report: dict) -> tuple[str, str]:
    attention = [z for z in report["zones"] if z["status"] == "low"]
    if not attention:
        score = report["farm_score"]
        return ("FARM OK", f"health {score if score is not None else '--'}/100")
    worst = attention[0]
    finding = worst["findings"][0]["class_name"] if worst["findings"] else "low health"
    t = worst["findings"][0].get("treatment") if worst["findings"] else None
    pest = t["pesticide"] if t else finding
    return (f"{worst['zone_id']} LOW {int(worst['health'])}", pest)


def write_files(report: dict, text: str) -> Path:
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "latest.txt").write_text(text)
    (config.REPORTS_DIR / "latest.json").write_text(json.dumps(report, indent=2))
    return config.REPORTS_DIR / "latest.txt"


def generate(conn, window_hours=None, to_lcd=False, quiet=False) -> dict:
    report = build_report(conn, window_hours=window_hours)
    text = render_text(report)
    write_files(report, text)
    if not quiet:
        print(text)
    if to_lcd:
        try:
            from . import lcd

            l1, l2 = render_lcd(report)
            lcd.show(l1, l2)
        except Exception as exc:
            print(f"[report] LCD update skipped ({exc})")
    return report


def main():
    ap = argparse.ArgumentParser(description="Acre on-device field report")
    ap.add_argument("--watch", action="store_true", help="refresh periodically")
    ap.add_argument("--interval", type=float, default=30.0, help="watch seconds")
    ap.add_argument("--window", type=float, default=None, help="trailing hours")
    ap.add_argument("--lcd", action="store_true", help="also show summary on the LCD")
    ap.add_argument("--quiet", action="store_true", help="write files, don't print")
    args = ap.parse_args()

    conn = local_db.connect()
    try:
        if args.watch:
            print(f"[report] watching, refresh every {args.interval:g}s "
                  f"(Ctrl-C to stop)")
            while True:
                generate(conn, args.window, to_lcd=args.lcd, quiet=args.quiet)
                time.sleep(args.interval)
        else:
            generate(conn, args.window, to_lcd=args.lcd, quiet=args.quiet)
    except KeyboardInterrupt:
        print("\n[report] stopped")


if __name__ == "__main__":
    main()
