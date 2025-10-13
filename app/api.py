from __future__ import annotations
from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
import csv

app = Flask(__name__)

ROOT = Path(__file__).resolve().parents[1]
EVENTS_DIR = ROOT / "data" / "events"
CSV_PATH = EVENTS_DIR / "events.csv"

@app.after_request
def add_cors_headers(resp):
    # Allow your phone to call this from Expo Go
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return resp


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


@app.get("/api/events")
def list_events():
    limit = int(request.args.get("limit", "100"))
    events = []

    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize fields
                ts = row.get("timestamp", "")
                label = row.get("label", "")
                distance = row.get("distance", "")
                bbox_x = row.get("bbox_x", "")
                bbox_y = row.get("bbox_y", "")
                bbox_w = row.get("bbox_w", "")
                bbox_h = row.get("bbox_h", "")
                img_path = row.get("image_path", "")

                # Build an absolute image URL your phone can load
                # Example: http://192.168.1.23:5000/events/2025-10-11_11-22-33_unknown.jpg
                filename = Path(img_path).name if img_path else ""
                base = request.host_url.rstrip("/")
                image_url = f"{base}/events/{filename}" if filename else ""

                events.append({
                    "timestamp": ts,
                    "label": label,
                    "distance": distance,
                    "bbox": {
                        "x": bbox_x, "y": bbox_y, "w": bbox_w, "h": bbox_h
                    },
                    "image_url": image_url,
                    "filename": filename,
                })

    # Newest first
    events.sort(key=lambda e: e["timestamp"], reverse=True)
    events = events[:limit]
    return jsonify({"events": events, "count": len(events)})


@app.get("/events/<path:filename>")
def serve_event_image(filename: str):
    return send_from_directory(EVENTS_DIR, filename, as_attachment=False)
