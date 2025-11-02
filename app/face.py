from __future__ import annotations
import cv2
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis

# We use InsightFace's "FaceAnalysis" helper to detect faces and compute embeddings.
# It auto-downloads small models on first use and caches them in ~/.insightface/models.

class FaceEngine:
    """
    Wraps detector + embedder in a tiny, testable interface.
    - detect_and_embed(frame_bgr) -> list of {bbox, score, embedding}
      bbox = (x, y, w, h), score ~ detection confidence, embedding = 512-dim vector (L2-normalized)
    """

    def __init__(
        self,
        providers: list[str] | None = None,
        det_size: tuple[int, int] = (320, 320),
        min_det_score: float = 0.60,
    ) -> None:
        # 'buffalo_l' = good default pipeline (detector + embedder)
        self.app = FaceAnalysis(name="buffalo_l", providers=providers or ["CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=det_size)
        self.min_det_score = float(min_det_score)

    def detect_and_embed(self, frame_bgr: np.ndarray, min_face_size: int = 80) -> list[dict]:
        faces = self.app.get(frame_bgr)  # returns a list of faces with bbox, det_score, embedding
        out: list[dict] = []

        for f in faces:
            x1, y1, x2, y2 = f.bbox.astype(int)
            w, h = x2 - x1, y2 - y1
            if w < min_face_size or h < min_face_size:
                continue

            score = float(getattr(f, "det_score", 1.0))
            if score < self.min_det_score:
                continue

            # Prefer normalized embedding if present
            emb = getattr(f, "normed_embedding", None)
            if emb is None or np.size(emb) == 0:
                emb = np.asarray(getattr(f, "embedding"), dtype=np.float32)
                # L2-normalize
                emb = emb / (np.linalg.norm(emb) + 1e-12)
            else:
                emb = np.asarray(emb, dtype=np.float32)

            out.append({
                "bbox": (int(x1), int(y1), int(w), int(h)),
                "score": score,
                "embedding": emb,
            })
        return out


def cosine_dist_to_gallery(emb: np.ndarray, gallery: np.ndarray) -> float:
    """Smaller is better. With normalized vectors, distance = 1 - max cosine similarity."""
    if gallery.size == 0:
        return float("inf")
    sims = gallery @ emb  # (N,) similarities
    best_sim = float(np.max(sims))
    return 1.0 - best_sim


def l2_dist_to_gallery(emb: np.ndarray, gallery: np.ndarray) -> float:
    """Euclidean distance to the closest gallery vector."""
    if gallery.size == 0:
        return float("inf")
    diffs = gallery - emb
    dists = np.sqrt(np.sum(diffs * diffs, axis=1))
    return float(np.min(dists))

def build_gallery_for_dir(dir_path: Path, engine: FaceEngine, min_face_size: int = 80) -> np.ndarray:
    paths = []
    for ext in ("*.jpg","*.jpeg","*.png","*.JPG","*.PNG"):
        paths.extend(dir_path.glob(ext))
    embs = []
    for p in paths:
        img = cv2.imread(str(p))
        if img is None:
            continue
        items = engine.detect_and_embed(img, min_face_size=min_face_size)
        if not items:
            continue
        best = max(items, key=lambda d: d["score"])
        embs.append(best["embedding"])
    if not embs:
        return np.zeros((0,512), dtype=np.float32)
    g = np.stack(embs, axis=0).astype(np.float32)
    g = g / (np.linalg.norm(g, axis=1, keepdims=True) + 1e-12)
    return g

def load_all_user_galleries(users: list[dict], engine: FaceEngine, enroll_root: Path, min_face_size: int = 80) -> dict[str, np.ndarray]:
    """Return {user_id: gallery_matrix}."""
    galleries = {}
    for u in users:
        uid = u["id"]
        g = build_gallery_for_dir(enroll_root / uid, engine, min_face_size=min_face_size)
        galleries[uid] = g
    return galleries

def best_match_across_users(emb: np.ndarray, galleries: dict[str, np.ndarray], metric="cosine"):
    """
    Return (user_id, distance) for the best match, or (None, inf) if none.
    """
    best_uid, best_dist = None, float("inf")
    for uid, gal in galleries.items():
        if gal.size == 0:
            continue
        if metric == "l2":
            d = l2_dist_to_gallery(emb, gal)
        else:
            d = cosine_dist_to_gallery(emb, gal)
        if d < best_dist:
            best_dist, best_uid = d, uid
    return best_uid, best_dist
