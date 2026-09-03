import base64

import cv2
import numpy as np

from app.services.rule_engine import FieldOutcome

STATUS_COLOR_BGR = {
    "pass": (79, 107, 47),   # verified green
    "warn": (61, 124, 156),  # brass/amber
    "fail": (43, 49, 165),   # seal red
}


def draw_detection_boxes(display_bgr: np.ndarray, outcomes: list[FieldOutcome]) -> np.ndarray:
    annotated = display_bgr.copy()
    for outcome in outcomes:
        color = STATUS_COLOR_BGR.get(outcome.status, (128, 128, 128))
        for box in outcome.boxes:
            cv2.rectangle(annotated, (int(box.x0), int(box.y0)), (int(box.x1), int(box.y1)), color, 3)
    return annotated


def image_to_b64_jpeg(image_bgr: np.ndarray, quality: int = 88) -> str:
    ok, buf = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Failed to encode image as JPEG")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def b64_jpeg_to_bgr(b64_str: str) -> np.ndarray:
    raw = base64.b64decode(b64_str)
    arr = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image data")
    return image
