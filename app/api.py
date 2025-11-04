from __future__ import annotations
from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
import csv
from werkzeug.utils import secure_filename
from .users import load_users, create_user, get_user, user_enroll_path, ENROLL_DIR
from .face import FaceEngine, load_all_user_galleries
import os

ENGINE = None
GALLERIES = {}
MIN_FACE_SIZE = 80

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

def init_face_engine():
    global ENGINE, GALLERIES
    if ENGINE is None:
        ENGINE = FaceEngine(providers=["CPUExecutionProvider"], det_size=(640, 640), min_det_score=0.60)
        GALLERIES = load_all_user_galleries(load_users(), ENGINE, ENROLL_DIR, min_face_size=MIN_FACE_SIZE)
        print("[INIT] Face engine initialized")

init_face_engine()

# @app.before_request
# def ensure_initialized():
#     """Lazy initialize once per process."""
#     global _initialized
#     if not _initialized:
#         with _init_lock:
#             if not _initialized:
#                 init_face_engine()
#                 _initialized = True

def refresh_galleries():
    global GALLERIES
    users = load_users()
    GALLERIES = load_all_user_galleries(users, ENGINE, ENROLL_DIR, min_face_size=MIN_FACE_SIZE)

@app.post("/api/users")
def api_create_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    user = create_user(name)
    # refresh galleries so new empty user exists
    refresh_galleries()
    return jsonify({"user": user}), 201

@app.get("/api/users")
def api_list_users():
    return jsonify({"users": load_users()})

ALLOWED_EXTS = {"jpg", "jpeg", "png", "JPG", "PNG"}

@app.post("/api/users/<user_id>/photos")
def api_upload_photos(user_id: str=None):
    u = get_user(user_id)
    if not u:
        return jsonify({"error": "user not found"}), 404

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "no files"}), 400

    save_dir = user_enroll_path(user_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for f in files:
        fname = secure_filename(f.filename or "")
        ext = fname.rsplit(".", 1)[-1] if "." in fname else ""
        if ext not in ALLOWED_EXTS:
            continue
        out = save_dir / fname
        idx = 1
        while out.exists():
            out = save_dir / f"{out.stem}_{idx}.{ext}"
            idx += 1
        f.save(out)
        saved.append(out.name)

    # rebuild galleries for this user
    refresh_galleries()
    return jsonify({"ok": True, "saved": saved, "user_id": user_id})
