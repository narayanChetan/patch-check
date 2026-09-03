"""
OCR wrapper around pytesseract (the real Tesseract engine, not the
weaker/less-configurable tesseract.js browser port).

image_to_data gives word-level text with confidence and pixel bounding
boxes in one call — this is the data the rule engine matches against and
the frontend draws detection boxes from.
"""
from dataclasses import dataclass

import numpy as np
import pytesseract
from pytesseract import Output

from app.core.config import MIN_OCR_CONFIDENCE


@dataclass
class OcrWord:
    text: str
    conf: float
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class OcrResult:
    words: list[OcrWord]       # confidence-filtered — safe for boxes/font measurement
    all_words: list[OcrWord]   # unfiltered, same order as full_text — for offset alignment
    full_text: str


def run_ocr(ocr_ready_gray: np.ndarray, lang: str = "eng") -> OcrResult:
    """Runs Tesseract on a preprocessed grayscale image.

    PSM 6 ("assume a single uniform block of text") works well for product
    labels, which are dense blocks of small print rather than a page of
    prose. OEM 3 uses the LSTM engine, Tesseract's most accurate model.

    Confidence handling: Tesseract sometimes gives a correctly-read word a
    low confidence score (e.g. a phone number partly obscured by glare).
    We keep ALL non-empty words in `full_text` so regex matching still has
    the best chance of finding a declaration, but only expose high-
    confidence words for drawing bounding boxes / font-size measurement —
    we don't want to draw a box (or measure font height) around text
    Tesseract itself wasn't confident it read correctly.
    """
    config = "--oem 3 --psm 6"
    data = pytesseract.image_to_data(
        ocr_ready_gray, lang=lang, config=config, output_type=Output.DICT
    )

    all_words: list[OcrWord] = []
    trusted_words: list[OcrWord] = []
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        conf_raw = data["conf"][i]
        try:
            conf = float(conf_raw)
        except (TypeError, ValueError):
            conf = -1.0
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        word = OcrWord(text=text, conf=conf, x0=float(x), y0=float(y), x1=float(x + w), y1=float(y + h))
        all_words.append(word)
        if conf >= MIN_OCR_CONFIDENCE:
            trusted_words.append(word)

    full_text = " ".join(w.text for w in all_words)
    return OcrResult(words=trusted_words, all_words=all_words, full_text=full_text)
