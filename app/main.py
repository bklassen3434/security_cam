import cv2
import numpy as np
from pathlib import Path
import time
import os
import sys
import argparse
import yaml
from dotenv import load_dotenv
from datetime import datetime
from .storage import save_snapshot, log_event_csv
from .config import load_config, update_config
from .video import VideoSource, to_gray_blur, detect_motion
from .face import FaceEngine, build_gallery_for_dir, cosine_dist_to_gallery, l2_dist_to_gallery
from .notifier import notify_telegram, render_body
from .users import load_users, ENROLL_DIR
from .face import load_all_user_galleries, best_match_across_users
from .engine_runtime import get_face_engine

def run():

    last_refresh = time.monotonic()
    refresh_every = 300.0

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--demo", action="store_true")
    args, _ = parser.parse_known_args()

    load_dotenv()
    cfg = load_config()

    if args.demo:
        try:
            with open("demo.yaml", "r") as f:
                demo_cfg = yaml.safe_load(f) or {}
            cfg = update_config(cfg, demo_cfg)
            print("[DEMO] Applied demo.yaml overrides")
        except Exception as e:
            print(f"[DEMO] Could not load demo.yaml: {e}")

    src_cfg = cfg.get("input", {})
    use_rtsp = src_cfg.get("source", "usb") == "rtsp"
    rtsp_url = src_cfg.get("rtsp_url", "") if use_rtsp else None

    cam = VideoSource(
        cfg.get("camera_index", src_cfg.get("camera_index", 0)),
        cfg.get("frame_width", 640),
        cfg.get("frame_height", 480),
        rtsp_url=rtsp_url
        )
    
    notify_cfg = cfg.get("notify", {})
    
    telegram_cfg = notify_cfg.get("telegram", {})
    send_telegram = telegram_cfg.get("enabled")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    events_cfg = cfg.get("events", {})
    events_dir = events_cfg.get("dir", "data/events")
    csv_path = events_cfg.get("csv_path", "data/events/events.csv")
    cooldown_sec = float(events_cfg.get("cooldown_sec", 5))

    last_event_t = 0.0  # monotonic seconds of last logged UNKNOWN

    prev_gray = None
    motion_cfg = cfg.get("motion", {})
    motion_enabled = motion_cfg.get("enabled", True)
    thr = motion_cfg.get("threshold", 25)
    min_area = motion_cfg.get("min_area", 1200)
    visualize = motion_cfg.get("visualize", True)

    face_cfg = cfg.get("face", {})
    face_enabled = face_cfg.get("enabled", True)
    engine = None
    if face_enabled:
        # engine = FaceEngine(
        #     providers=["CPUExecutionProvider"],
        #     det_size=tuple(face_cfg.get("det_size", [640, 640])),
        #     min_det_score=float(face_cfg.get("min_det_score", 0.60)),
        # )
        engine = get_face_engine()

    users = load_users()
    galleries = load_all_user_galleries(users, engine, ENROLL_DIR, min_face_size=face_cfg.get("min_face_size", 80))
    id_to_name = {u["id"]: u["name"] for u in users}
    
    if face_enabled and engine is not None:
        enroll_dir = face_cfg.get("enroll_dir")
        gallery_cache = Path(enroll_dir) / "gallery.npy"
        if gallery_cache.exists():
            gallery = np.load(gallery_cache)
            print(f"[Face] Loaded cached gallery with {gallery.shape[0]} embeddings from {gallery_cache}")
        else:
            gallery = build_gallery_for_dir(Path(enroll_dir), engine, min_face_size=face_cfg.get("min_face_size", 80))
            print(f"[Face] Built new gallery with {gallery.shape[0]} embeddings from {enroll_dir}")
            np.save(gallery_cache, gallery)

    # Face recognition labels
    match_metric = face_cfg.get("match_metric", "cosine").lower()
    max_distance = float(face_cfg.get("max_distance", 0.45))

    frame_idx = 0
    last_faces = []

    try:
        while True:
            if time.monotonic() - last_refresh > refresh_every:
                users = load_users()
                galleries = load_all_user_galleries(users, engine, ENROLL_DIR, min_face_size=face_cfg.get("min_face_size", 80))
                id_to_name = {u["id"]: u["name"] for u in users}
                last_refresh = time.monotonic()

            frame = cam.read()
            frame_idx += 1
            gray = to_gray_blur(frame)

            if prev_gray is None:
                prev_gray = gray
                if cfg.get("show_window", True):
                    cv2.imshow("SecurityCam (Preview)", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                continue

            # --- MOTION DETECTION ---
            if motion_enabled:
                motion, bbox, mask = detect_motion(prev_gray, gray, thr, min_area)
            else:
                motion, bbox, mask = False, None, None

            # --- FACE DETECTION (first pass: just draw boxes) ---
            if motion and face_enabled and engine is not None and frame_idx % 3 == 0:
                last_faces = engine.detect_and_embed(frame, min_face_size=face_cfg.get("min_face_size", 80))
            if not motion:
                last_faces = []
            faces = last_faces

            unknown_candidates = []
            labeled_faces = []

            # Draw overlays if you want to see it
            if visualize and cfg.get("show_window", True):

                # Face boxes (blue)
                for f in faces:
                    fx, fy, fw, fh = f["bbox"]
                    emb = f["embedding"]

                    # best match across all users
                    uid, dist = best_match_across_users(emb, galleries, metric=match_metric)
                    if uid is not None and dist <= max_distance:
                        label = id_to_name.get(uid, uid)
                    else:
                        label = "UNKNOWN"

                    labeled_faces.append((label, dist, (fx, fy, fw, fh)))

                    if label == "UNKNOWN":
                        unknown_candidates.append((dist, (fx, fy, fw, fh), emb))

                    for label, dist, (fx, fy, fw, fh) in labeled_faces:
                        color = (0, 255, 0) if label != "UNKNOWN" else (0, 0, 255)
                        cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), color, 2)
                        cv2.putText(frame, f"{label}", (fx, fy + fh + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


                # After reviewing all faces, decide whether to log one UNKNOWN
                now_mono = time.monotonic()
                if unknown_candidates and (now_mono - last_event_t >= cooldown_sec):
                    # Pick the closest UNKNOWN
                    unknown_candidates.sort(key=lambda t: t[0])
                    best_dist, best_bbox, _ = unknown_candidates[0]

                    image_path = save_snapshot(frame, events_dir, label="unknown")

                    # Write CSV row
                    log_event_csv(csv_path, {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "label": "UNKNOWN",
                        "distance": best_dist,
                        "bbox": best_bbox,
                        "image_path": image_path,
                    })

                    # Telegram notification
                    if send_telegram:
                        msg_text  = render_body(telegram_cfg.get("body_template", "Unknown face at {time}"))
                        notify_telegram(bot_token, chat_id, image_path, msg_text)

                    print(f"[EVENT] UNKNOWN logged, d={best_dist:.3f}, saved={bool(image_path)}")
                    last_event_t = now_mono
                
                cv2.imshow("SecurityCam (Preview)", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # IMPORTANT: update the previous frame for next iteration
            prev_gray = gray

    finally:
        cam.release()
        cv2.destroyAllWindows()
