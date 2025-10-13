import cv2
import numpy as np

class VideoSource:
    def __init__(self, camera_index: int, width: int, height: int, rtsp_url: str | None = None):
        if rtsp_url:
            self.cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        else:
            self.cap = cv2.VideoCapture(camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video source")

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Failed to read frame from camera")
        return frame  # BGR

    def release(self):
        if self.cap:
            self.cap.release()

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
