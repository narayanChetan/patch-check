import cv2
import numpy as np

from app.services import ocr_engine, preprocessing, rule_engine


def _run_pipeline(image_bytes: bytes):
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    _, ocr_ready = preprocessing.preprocess_for_ocr(img)
    ocr = ocr_engine.run_ocr(ocr_ready)
    outcomes = rule_engine.evaluate(ocr)
    return ocr, outcomes


def test_compliant_label_detects_mrp(compliant_medicine_label_bytes):
    """Regression test for the exact bug reported: a real MRP on the label
    must be detected, not silently marked missing."""
    _, outcomes = _run_pipeline(compliant_medicine_label_bytes)
    mrp_outcome = next(o for o in outcomes if o.key == "mrp")
    assert mrp_outcome.status == "pass", f"Expected MRP to pass, got: {mrp_outcome.note}"


def test_compliant_label_overall_verdict_not_fail(compliant_medicine_label_bytes):
    _, outcomes = _run_pipeline(compliant_medicine_label_bytes)
    verdict = rule_engine.compute_verdict(outcomes)
    assert verdict in ("pass", "warn"), "A fully-declared label should not FAIL outright"


def test_incomplete_label_flags_missing_mrp(incomplete_label_bytes):
    _, outcomes = _run_pipeline(incomplete_label_bytes)
    mrp_outcome = next(o for o in outcomes if o.key == "mrp")
    assert mrp_outcome.status == "fail"
    verdict = rule_engine.compute_verdict(outcomes)
    assert verdict == "fail"


def test_mrp_without_inclusive_phrase_warns():
    """Rule 2(m) requires the 'inclusive of all taxes' qualifier — an MRP
    printed without it should warn, not silently pass."""
    from tests.conftest import make_label_image

    image_bytes = make_label_image([
        "PRODUCT X",
        "Net Qty: 200 g",
        "MRP Rs. 99.00",
        "Mfg By: Test Co",
        "Consumer Care: 011-12345678",
    ])
    _, outcomes = _run_pipeline(image_bytes)
    mrp_outcome = next(o for o in outcomes if o.key == "mrp")
    assert mrp_outcome.status == "warn"
    assert "inclusive" in mrp_outcome.note.lower()


def test_every_field_has_a_real_rule_citation():
    """Guards against a field definition being added without a genuine
    rule reference — citations are what make this tool trustworthy."""
    for f in rule_engine.FIELDS:
        assert f["rule"], f"Field {f['key']} is missing a rule citation"
        assert "rule" in f["rule"].lower() or "order" in f["rule"].lower()
