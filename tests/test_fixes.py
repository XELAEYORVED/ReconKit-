"""Regression tests for the CLI compare command, target validation and live API keys."""

import asyncio

from click.testing import CliRunner
from fastapi.testclient import TestClient

from reconkit.cli import cli
from reconkit.config import get_settings
from reconkit.engine import ReconEngine
from server.main import app


def test_invalid_target_is_rejected_upfront():
    with TestClient(app) as c:
        r = c.post("/api/scans", json={"target": "Alexandre devroye"})
        assert r.status_code == 400
        assert "not a domain" in r.json()["detail"]


def test_api_key_applies_without_restart():
    with TestClient(app) as c:
        assert not get_settings().hibp_api_key
        r = c.put("/api/settings/api-keys", json={"service": "hibp", "key": "test-key"})
        assert r.status_code == 200
        assert get_settings().hibp_api_key == "test-key"
        mods = {m["name"]: m for m in c.get("/api/settings/modules").json()}
        assert mods["leak_check"]["available"] is True

        c.delete("/api/settings/api-keys/hibp")
        assert get_settings().hibp_api_key == ""


def test_cli_compare_runs():
    async def two_scans():
        eng = ReconEngine()
        a = await eng.run_scan("example.com", modules=["fake"])
        b = await eng.run_scan("example.com", modules=["fake"])
        return a["scan_id"], b["scan_id"]

    id1, id2 = asyncio.run(two_scans())
    res = CliRunner().invoke(cli, ["compare", id1, id2])
    assert res.exit_code == 0, res.output
    assert "Threat score" in res.output
