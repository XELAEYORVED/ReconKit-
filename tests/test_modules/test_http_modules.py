"""Module tests with mocked HTTP (respx) — no real network calls."""

import httpx
import pytest
import respx

from reconkit.modules.cert_transparency import CertTransparencyModule
from reconkit.modules.headers_audit import HeadersAuditModule
from reconkit.modules.leak_check import LeakCheckModule
from reconkit.modules.reputation import ReputationModule
from reconkit.modules.shodan_recon import ShodanModule

pytestmark = pytest.mark.asyncio


@respx.mock
async def test_cert_transparency_parses_sans():
    sample = [
        {"issuer_name": "C=US, O=Let's Encrypt", "name_value": "a.example.com\nexample.com",
         "serial_number": "01", "not_before": "2024-01-01", "not_after": "2024-04-01",
         "common_name": "example.com", "id": 1},
        {"issuer_name": "C=US, O=Let's Encrypt", "name_value": "*.example.com",
         "serial_number": "02", "not_before": "2024-02-01", "not_after": "2024-05-01",
         "common_name": "example.com", "id": 2},
    ]
    respx.get(url__startswith="https://crt.sh/").mock(
        return_value=httpx.Response(200, json=sample)
    )
    res = await CertTransparencyModule().run("example.com")
    assert res.status == "ok"
    assert res.data["unique_certificates"] == 2
    assert "a.example.com" in res.data["san_hostnames"]


@respx.mock
async def test_headers_audit_scores_missing():
    respx.get("https://example.com").mock(
        return_value=httpx.Response(
            200,
            headers={"server": "nginx", "strict-transport-security": "max-age=63072000"},
            text="<html></html>",
        )
    )
    res = await HeadersAuditModule().run("example.com")
    assert res.status == "ok"
    assert "Content-Security-Policy" in res.data["missing"]
    assert "HSTS" in res.data["present"]
    assert 0 <= res.data["score"] <= 100
    assert res.data["grade"] in ("A", "B", "C", "D", "F")


@respx.mock
async def test_shodan_keyless_internetdb():
    # No key configured -> falls back to InternetDB.
    respx.get(url__startswith="https://internetdb.shodan.io/").mock(
        return_value=httpx.Response(200, json={
            "ports": [80, 443, 22], "hostnames": ["example.com"],
            "vulns": ["CVE-2021-1234"], "cpes": [], "tags": [],
        })
    )
    res = await ShodanModule().run("8.8.8.8")
    assert res.status == "ok"
    assert res.data["source"] == "internetdb-keyless"
    assert 443 in res.data["ports"]
    assert "CVE-2021-1234" in res.data["vulns"]


async def test_leak_check_skips_without_key():
    res = await LeakCheckModule().run("user@example.com")
    assert res.status == "skipped"
    assert "HIBP" in (res.error or "")


async def test_reputation_skips_without_keys():
    res = await ReputationModule().run("example.com")
    assert res.status == "skipped"
