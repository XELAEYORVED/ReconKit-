"""API integration tests (hermetic, using the fake module)."""

import time

from fastapi.testclient import TestClient

from server.main import app


def test_health_and_modules():
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        mods = c.get("/api/scans/modules").json()
        assert any(m["name"] == "fake" for m in mods)


def test_scan_lifecycle_and_export():
    with TestClient(app) as c:
        r = c.post("/api/scans", json={"target": "example.com", "modules": ["fake"]})
        assert r.status_code == 202
        sid = r.json()["scan_id"]

        for _ in range(40):
            scan = c.get(f"/api/scans/{sid}").json()
            if scan["status"] == "completed":
                break
            time.sleep(0.1)
        assert scan["status"] == "completed"
        assert scan["results"][0]["module_name"] == "fake"

        stix = c.get(f"/api/reports/{sid}", params={"format": "stix"})
        assert stix.status_code == 200
        assert b"bundle" in stix.content

        c.delete(f"/api/scans/{sid}")
        assert c.get(f"/api/scans/{sid}").status_code == 404
