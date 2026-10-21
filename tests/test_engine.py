"""Engine orchestration tests (hermetic, using the fake module)."""

import pytest

from reconkit.database import init_db
from reconkit.engine import ReconEngine
from reconkit.models import TargetType
from reconkit.utils import enrichment
from reconkit.modules.base import ModuleResult

pytestmark = pytest.mark.asyncio


async def test_run_scan_persists_and_enriches():
    await init_db()
    events = []

    async def cb(e):
        events.append(e["event"])

    eng = ReconEngine(progress_cb=cb)
    out = await eng.run_scan("example.com", modules=["fake"], target_type=TargetType.DOMAIN)

    assert out["scan_id"].startswith("scan-")
    assert out["results"][0]["module_name"] == "fake"
    assert out["results"][0]["status"] == "ok"
    assert "scan_start" in events and "scan_complete" in events
    # Graph should contain the target node + the derived IP node.
    labels = {n["label"] for n in out["graph"]["nodes"]}
    assert "example.com" in labels


async def test_unknown_module_yields_no_modules():
    eng = ReconEngine()
    with pytest.raises(ValueError):
        await eng.run_scan("example.com", modules=["does_not_exist"],
                           target_type=TargetType.DOMAIN, persist=False)


def test_threat_score_rewards_missing_headers():
    results = [
        ModuleResult(module_name="headers", target="x", status="ok",
                     data={"missing": ["HSTS", "CSP", "X-Frame-Options"],
                           "cors_wildcard": True, "cookie_issues": []}),
    ]
    score, factors = enrichment.compute_threat_score(results)
    assert score > 0
    assert any("headers" in f["reason"] for f in factors)


def test_risk_level_bands():
    assert enrichment.risk_level(5) == "low"
    assert enrichment.risk_level(25) == "medium"
    assert enrichment.risk_level(50) == "high"
    assert enrichment.risk_level(80) == "critical"
