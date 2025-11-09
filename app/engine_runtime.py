from __future__ import annotations
import os
import threading
from typing import Optional, Tuple
import numpy as np
from .face import FaceEngine

_engine: Optional[FaceEngine] = None
_lock = threading.Lock()

def _env_tuple(name: str, default: Tuple[int, int]) -> Tuple[int, int]:
    raw = os.getenv(name, "")
    if raw:
        try:
            parts = raw.split(",")
            return (int(parts[0]), int(parts[1]))
        except Exception:
            pass
    return default

def get_face_engine() -> FaceEngine:
    global _engine
    if _engine is not None:
        return _engine

    with _lock:
        if _engine is None:
            model_name = os.getenv("INSIGHTFACE_MODEL", "buffalo_l")
            providers = [p.strip() for p in os.getenv("ONNX_PROVIDERS", "CPUExecutionProvider").split(",") if p.strip()]
            det_size = _env_tuple("INSIGHTFACE_DET_SIZE", (320, 320))
            min_det_score = float(os.getenv("MIN_DET_SCORE", "0.60"))

            # Construct the engine
            _engine = FaceEngine(
                providers=providers,
                det_size=det_size,
                min_det_score=min_det_score,
            )
    return _engine
