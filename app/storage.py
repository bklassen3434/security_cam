from __future__ import annotations
import csv
from pathlib import Path
from datetime import datetime
import cv2
import os

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def timestamp_str() -> str:
    # Safe for filenames
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def save_snapshot(frame_bgr, out_dir: str | Path, label: str = "unknown") -> str:
    out_dir = ensure_dir(out_dir)
    fname = f"{timestamp_str()}_{label}.jpg"
    fpath = out_dir / fname
    cv2.imwrite(str(fpath), frame_bgr)
    return str(fpath)

def log_event_csv(csv_path: str | Path, row: dict) -> None:
    csv_path = Path(csv_path)
    ensure_dir(csv_path.parent)

    write_header = not csv_path.exists()

    fieldnames = [
        "timestamp",
        "label",
        "distance",
        "bbox_x",
        "bbox_y",
        "bbox_w",
        "bbox_h",
        "image_path",
    ]

    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": row.get("timestamp", ""),
            "label": row.get("label", ""),
            "distance": f"{row.get('distance', float('nan')):.3f}" if isinstance(row.get("distance", None), (float,int)) else row.get("distance",""),
            "bbox_x": row.get("bbox", (None, None, None, None))[0],
            "bbox_y": row.get("bbox", (None, None, None, None))[1],
            "bbox_w": row.get("bbox", (None, None, None, None))[2],
            "bbox_h": row.get("bbox", (None, None, None, None))[3],
            "image_path": row.get("image_path", ""),
        })
