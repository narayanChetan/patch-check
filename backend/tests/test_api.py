import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _login(client, username="inspector", password="inspector123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_rejects_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "inspector", "password": "wrong"})
    assert r.status_code == 401


def test_scan_requires_auth(client, compliant_medicine_label_bytes):
    r = client.post("/api/scan", files={"file": ("l.jpg", compliant_medicine_label_bytes, "image/jpeg")})
    assert r.status_code == 401


def test_scan_rejects_non_image(client):
    token = _login(client)
    r = client.post(
        "/api/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("f.txt", b"not an image", "text/plain")},
    )
    assert r.status_code == 400


def test_full_scan_and_report_flow(client, compliant_medicine_label_bytes):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/scan", headers=headers,
        files={"file": ("label.jpg", compliant_medicine_label_bytes, "image/jpeg")},
        data={"product_name": "Test Syrup", "save": "true"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["verdict"] in ("pass", "warn", "fail")
    assert len(data["field_results"]) >= 5

    pdf = client.get(f"/api/scan/{data['id']}/report.pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert len(pdf.content) > 1000


def test_inspector_cannot_see_other_inspectors_scans(client, compliant_medicine_label_bytes):
    """Role-based access: an inspector's ledger should never show another
    inspector's scans, only admins get the cross-user view."""
    insp_token = _login(client, "inspector", "inspector123")
    client.post(
        "/api/scan", headers={"Authorization": f"Bearer {insp_token}"},
        files={"file": ("l.jpg", compliant_medicine_label_bytes, "image/jpeg")},
        data={"product_name": "Inspector Scan", "save": "true"},
    )

    admin_token = _login(client, "admin", "admin123")
    admin_ledger = client.get("/api/ledger", headers={"Authorization": f"Bearer {admin_token}"}).json()
    inspector_ledger = client.get("/api/ledger", headers={"Authorization": f"Bearer {insp_token}"}).json()

    assert len(admin_ledger) >= len(inspector_ledger)
    assert all(e["inspector_username"] == "inspector" for e in inspector_ledger)


def test_ledger_search_by_product_name(client, harmful_ingredient_label_bytes):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/scan", headers=headers,
        files={"file": ("bread.jpg", harmful_ingredient_label_bytes, "image/jpeg")},
        data={"product_name": "ZZZ Unique Bread Name", "save": "true"},
    )
    results = client.get("/api/ledger?q=ZZZ Unique", headers=headers).json()
    assert any("ZZZ Unique" in r["product_name"] for r in results)


def test_delete_scan_removes_it_from_ledger(client, compliant_medicine_label_bytes):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/api/scan", headers=headers,
        files={"file": ("l.jpg", compliant_medicine_label_bytes, "image/jpeg")},
        data={"product_name": "To Delete", "save": "true"},
    )
    scan_id = r.json()["id"]
    del_r = client.delete(f"/api/ledger/{scan_id}", headers=headers)
    assert del_r.status_code == 200
    detail_r = client.get(f"/api/ledger/{scan_id}", headers=headers)
    assert detail_r.status_code == 404
