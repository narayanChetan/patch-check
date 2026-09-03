import io

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont


def _font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def make_label_image(lines: list[str], rotate_deg: float = 0.0, add_noise: bool = False) -> bytes:
    """Builds a synthetic product-label photo for pipeline testing. Real
    photos are messier than this, but a clean synthetic label with known
    ground truth is exactly what's needed to catch regressions in the rule
    engine and OCR wiring without requiring real product photos in the repo."""
    img = Image.new("RGB", (900, 80 + 40 * len(lines)), "white")
    draw = ImageDraw.Draw(img)
    font = _font(24)
    y = 30
    for line in lines:
        draw.text((40, y), line, fill="black", font=font)
        y += 40

    if rotate_deg:
        img = img.rotate(rotate_deg, expand=True, fillcolor="white")
    if add_noise:
        arr = np.array(img).astype(np.int16)
        noise = np.random.normal(0, 8, arr.shape).astype(np.int16)
        arr = np.clip(arr + noise, 0, 255).astype("uint8")
        img = Image.fromarray(arr)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


@pytest.fixture
def compliant_medicine_label_bytes():
    return make_label_image([
        "COUGHEZE SYRUP",
        "Manufactured by: Sunrise Pharma Pvt Ltd,",
        "Plot 12, MIDC, Nashik, Maharashtra - 422010",
        "Net Quantity: 100 ml",
        "MRP Rs. 85.00 incl. of all taxes",
        "Mfg. Date: 03/2026",
        "Consumer Care: 022-98765432",
    ], rotate_deg=2.0, add_noise=True)


@pytest.fixture
def incomplete_label_bytes():
    """Deliberately missing MRP and consumer care — should fail the rule engine."""
    return make_label_image([
        "MYSTERY SNACKS",
        "Net Wt: 50 g",
    ])


@pytest.fixture
def harmful_ingredient_label_bytes():
    return make_label_image([
        "TASTY BAKERY BREAD",
        "Ingredients: Wheat Flour, Sugar, Potassium Bromate,",
        "Sodium Benzoate (0.05%), Monosodium Glutamate, Salt",
        "Net Quantity: 400 g",
        "MRP Rs. 45.00 incl. of all taxes",
        "Mfg By: Tasty Foods Ltd, Pune",
        "Consumer Care: 022-98765432",
    ])
