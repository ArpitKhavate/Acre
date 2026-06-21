#!/usr/bin/env python3
"""Webcam demo: scan plants, press F to open the live farm health report.

Simulates the future QNX → laptop report flow locally:
  1. Point webcam at plants/weeds (hold steady ~2s per scan).
  2. After enough detections, press F in the camera window.
  3. Browser opens http://localhost:8787 with AI summary, top pest, pesticide.

Usage:
    python scripts/webcam_farm_demo.py
    python scripts/webcam_farm_demo.py --min-scans 5 --conf 0.55

Keys:  F = generate report & open browser   q = quit
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2  # noqa: E402

GREEN = (0, 200, 0)
RED = (0, 0, 255)
AMBER = (0, 170, 255)
WHITE = (255, 255, 255)
CYAN = (255, 220, 100)

REPORT_HTML = ROOT / "web" / "live" / "index.html"
DEFAULT_PORT = 8787

# Shared state for the HTTP handler
_state = {"report": None, "session_scans": 0, "min_scans": 3}


class _ReportHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            if not REPORT_HTML.is_file():
                self.send_error(404, "report page missing")
                return
            body = REPORT_HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/report/latest":
            report = _state.get("report")
            if report:
                self._json(200, report)
            else:
                self._json(200, {"ready": False, "session_scans": _state["session_scans"],
                                 "min_scans": _state["min_scans"]})
            return
        if path == "/api/session":
            self._json(200, {
                "scans": _state["session_scans"],
                "min_scans": _state["min_scans"],
                "ready": bool(_state.get("report")),
            })
            return
        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()


def _start_server(port: int) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("0.0.0.0", port), _ReportHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


def _banner(frame, lines, color=WHITE):
    h = 24 + 22 * len(lines)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], h), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        cv2.putText(frame, line, (8, 20 + i * 22), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, color, 2)


def main():
    ap = argparse.ArgumentParser(description="Webcam farm demo + live report (press F)")
    ap.add_argument("--source", default="0")
    ap.add_argument("--conf", type=float, default=0.55)
    ap.add_argument("--min-scans", type=int, default=3,
                    help="plant/weed detections needed before F generates report")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--scan-interval", type=float, default=2.0,
                    help="seconds between logged scans when plant/weed visible")
    args = ap.parse_args()

    from edge import detect as edet
    from edge import health_score, session_report

    _state["min_scans"] = args.min_scans
    srv = _start_server(args.port)
    url = f"http://127.0.0.1:{args.port}"
    print(f"[demo] report server {url}")
    print(f"[demo] scan {args.min_scans}+ plants/weeds, then press F in the camera window")

    detector = edet.Detector()
    if not detector.detector.ok:
        print("[demo] WARNING: detector.onnx missing — scans may be empty")

    cap = cv2.VideoCapture(int(args.source) if str(args.source).isdigit() else args.source)
    if not cap.isOpened():
        raise SystemExit(f"could not open camera {args.source!r}")

    scans: list[dict] = []
    last_log = 0.0
    flash_until = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            result = detector.analyze(frame, classify_pests=True, conf_thresh=args.conf)
            score = health_score.compute(result)
            now = time.time()

            if score is not None and now - last_log >= args.scan_interval:
                scans.append(session_report.scan_from_result(score, result))
                _state["session_scans"] = len(scans)
                last_log = now
                print(f"[demo] logged scan {len(scans)}: {score.type}:{score.class_name} "
                      f"health={score.score}")

            for b in result.weed_boxes:
                x, y, w, h = b.xywh
                cv2.rectangle(frame, (x, y), (x + w, y + h), RED, 2)
                cv2.putText(frame, f"weed {b.conf:.2f}", (x, max(y - 6, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 2)
            if result.plant_box is not None:
                x, y, w, h = result.plant_box.xywh
                col = GREEN if result.is_healthy else AMBER
                cv2.rectangle(frame, (x, y), (x + w, y + h), col, 2)
                lbl = result.disease_class or "crop"
                cv2.putText(frame, lbl, (x, max(y - 6, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)

            n = len(scans)
            need = max(0, args.min_scans - n)
            if need:
                status = f"Scans: {n}/{args.min_scans}  —  point at plants"
                hint = "Press F when ready (need more scans)" if n < args.min_scans else "Press F for report"
            else:
                status = f"Scans: {n}  —  ready for report"
                hint = "Press F to open farm report"
            _banner(frame, [status, hint], CYAN if need else GREEN)

            if now < flash_until:
                cv2.putText(frame, "REPORT OPENED", (frame.shape[1] // 2 - 120, frame.shape[0] // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, GREEN, 2)

            cv2.imshow("Acre farm demo (F = report, q = quit)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in (ord("f"), ord("F")):
                if n < args.min_scans:
                    print(f"[demo] need {args.min_scans - n} more scan(s) — hold camera on plants")
                    continue
                try:
                    report = session_report.build_session_report(scans)
                    _state["report"] = report
                    webbrowser.open(url)
                    flash_until = time.time() + 2.0
                    print(f"[demo] report generated — farm health {report['farm_health']}/100")
                    print(f"       top pest: {report['top_pest']}")
                    print(f"       pesticide: {report['top_pesticide']}")
                except Exception as exc:
                    print(f"[demo] report failed: {exc}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        srv.shutdown()


if __name__ == "__main__":
    main()
