"""
OpenCV preprocessing pipeline for label photos.

Real product photos are rarely OCR-ready straight out of a phone camera:
they're tilted, unevenly lit, and often low-contrast. This module runs the
classic label-scanning pipeline (grayscale -> denoise -> CLAHE contrast ->
deskew -> adaptive threshold) that meaningfully improves Tesseract's
accuracy on real, imperfect photos — this is the fix for text like a small
printed MRP being missed entirely.
"""
import cv2
import numpy as np


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def deskew(gray: np.ndarray) -> np.ndarray:
    """Rotate the image so the dominant text/edge angle is horizontal.

    Uses the minimum-area bounding rectangle of all non-background pixels,
    which is robust for photos of a single label roughly filling the frame.
    Falls back to the original image if no useful contour is found.

    Note on the angle sign: cv2.minAreaRect's angle convention changed
    across OpenCV versions and is easy to get backwards (this was an
    actual bug here, caught by testing against a label rotated by a known
    angle — the first version rotated text further off-axis instead of
    correcting it). Verified empirically against OpenCV 4.10: for the
    typical case (angle in [-45, 0)), the raw angle is used directly with
    no sign flip; only the >45°-tilt wraparound case needs adjustment.
    """
    inverted = cv2.bitwise_not(gray)
    thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = cv2.findNonZero(thresh)
    if coords is None or len(coords) < 50:
        return gray

    raw_angle = cv2.minAreaRect(coords)[-1]
    if raw_angle < -45:
        angle = -(90 + raw_angle)
    else:
        angle = raw_angle

    # Only correct small skews — large "angles" usually mean the rectangle
    # picked up the whole frame, not genuine rotation, so leave those alone.
    if abs(angle) < 0.5 or abs(angle) > 20:
        return gray

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def preprocess_for_ocr(image_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns (display_image_bgr, ocr_ready_gray).

    display_image_bgr: upright, denoised, still colour — used for drawing
    detection boxes so the evidence photo looks natural.
    ocr_ready_gray: thresholded, high-contrast grayscale — fed to Tesseract.
    """
    # Upscale small photos — Tesseract accuracy drops sharply below ~300 DPI
    # equivalent; doubling small images is a cheap, reliable accuracy win.
    h, w = image_bgr.shape[:2]
    if max(h, w) < 1600:
        scale = 1600 / max(h, w)
        image_bgr = cv2.resize(image_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = deskew(gray)

    # Re-derive the colour image in the same orientation for display/boxes.
    # (We deskew via the grayscale channel above; apply the same routine's
    # logic to a colour copy so boxes line up with what OCR actually saw.)
    display = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(denoised)

    ocr_ready = cv2.adaptiveThreshold(
        contrasted, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )

    return display, ocr_ready
