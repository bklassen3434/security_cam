import cv2
import numpy as np

class VideoSource:
    def __init__(self, camera_index: int, width: int, height: int, rtsp_url: str | None = None):
        self.cap = cv2.VideoCapture(rtsp_url if rtsp_url else camera_index)
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError("Could not open video source")

        _set_if_supported(self.cap, cv2.CAP_PROP_FRAME_WIDTH,  width)
        _set_if_supported(self.cap, cv2.CAP_PROP_FRAME_HEIGHT, height)
        _set_if_supported(self.cap, cv2.CAP_PROP_FPS, 15)

        ok, _ = self.cap.read()
        if not ok:
            raise RuntimeError("Camera opened but no frames. Try a different camera_index (0,1,2).")

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Failed to read frame from camera")
        return frame

    def release(self):
        if self.cap:
            self.cap.release()

def _set_if_supported(cap, prop, value):
    try:
        cap.set(prop, value)
    except Exception:
        pass

def to_gray_blur(frame_bgr):
    """Fast pre-processing: grayscale + Gaussian blur to reduce noise."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)  # large kernel smooths flicker
    return gray

def detect_motion(prev_gray, curr_gray, threshold: int, min_area: int):
    """
    Returns (motion_bool, bbox, mask)
    - motion_bool: True if any contour >= min_area
    - bbox: (x, y, w, h) of the largest moving blob or None
    - mask: binary image of motion (useful for debugging)
    """
    # Pixel-wise difference
    delta = cv2.absdiff(prev_gray, curr_gray)

    # Threshold to isolate "changed" pixels
    _, mask = cv2.threshold(delta, threshold, 255, cv2.THRESH_BINARY)

    # Fill gaps and smooth the mask
    mask = cv2.dilate(mask, None, iterations=2)

    # Find blobs
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion = False
    best_bbox = None
    best_area = 0

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if area > best_area:
            best_area = area
            best_bbox = (x, y, w, h)
            motion = True

    return motion, best_bbox, mask
