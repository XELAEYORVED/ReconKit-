"""Tests for network_map (RIPEstat), wayback fallback and email_profile — no real network."""

import httpx
import pytest
import respx

from reconkit.modules.email_profile import EmailProfileModule
from reconkit.modules.network_map import NetworkMapModule
from reconkit.modules.wayback_machine import WaybackModule

pytestmark = pytest.mark.asyncio


def _ripe(data):
    return httpx.Response(200, json={"data": data})


@respx.mock
async def test_network_map_uses_ripestat():
    base = "https://stat.ripe.net/data/"
    respx.get(url__startswith=base + "network-info/").mock(
        return_value=_ripe({"asns": ["15169"], "prefix": "8.8.8.0/24"}))
    respx.get(url__startswith=base + "as-overview/").mock(
        return_value=_ripe({"holder": "GOOGLE - Google LLC", "block": {"desc": "Assigned by ARIN"}}))
    respx.get(url__startswith=base + "rir-stats-country/").mock(
        return_value=_ripe({"located_resources": [{"location": "US"}]}))
    respx.get(url__startswith=base + "announced-prefixes/").mock(
        return_value=_ripe({"prefixes": [{"prefix": "8.8.8.0/24"}, {"prefix": "8.8.4.0/24"}]}))
    respx.get(url__startswith=base + "asn-neighbours/").mock(
        return_value=_ripe({"neighbours": [{"asn": 3356, "type": "left", "power": 9},
                                           {"asn": 64500, "type": "right", "power": 1}],
                            "neighbour_counts": {"left": 1, "right": 1}}))

    res = await NetworkMapModule().run("8.8.8.8")
    assert res.status == "ok"
    assert res.data["asn"]["asn"] == 15169
    assert res.data["asn"]["name"] == "GOOGLE"
    assert res.data["asn"]["country"] == "US"
    assert res.data["prefix_count"] == 2
    assert res.data["peers"]["upstreams"] == [{"asn": 3356, "name": None}]


@respx.mock
async def test_wayback_falls_back_when_cdx_down(monkeypatch):
    async def no_sleep(_):
        return None

    monkeypatch.setattr("asyncio.sleep", no_sleep)
    respx.get(url__startswith="https://web.archive.org/cdx/").mock(
        return_value=httpx.Response(503))
    respx.get(url__startswith="https://archive.org/wayback/available").mock(
        return_value=httpx.Response(200, json={"archived_snapshots": {"closest": {
            "available": True, "url": "http://web.archive.org/web/2026/https://example.com/",
            "timestamp": "20261023120000"}}}))

    res = await WaybackModule().run("example.com")
    assert res.status == "ok"
    assert res.data["last_capture"] == "20261023120000"
    assert "note" in res.data


@respx.mock
async def test_email_profile_without_keys(monkeypatch):
    async def fake_txt(self, resolver, name, rtype="TXT"):
        return {
            ("example.org", "MX"): ["10 mx.example.org."],
            ("example.org", "TXT"): ["v=spf1 -all"],
            ("_dmarc.example.org", "TXT"): ["v=DMARC1; p=reject"],
        }.get((name, rtype), [])

    monkeypatch.setattr(EmailProfileModule, "_txt", fake_txt)
    respx.get(url__startswith="https://en.gravatar.com/").mock(
        return_value=httpx.Response(200, json={"entry": [{
            "profileUrl": "https://gravatar.com/jane", "preferredUsername": "jane",
            "accounts": [{"shortname": "github", "url": "https://github.com/jane"}]}]}))

    res = await EmailProfileModule().run("jane@example.org")
    assert res.status == "ok"
    assert res.data["provider_type"] == "custom_domain"
    assert res.data["can_receive_mail"] is True
    assert res.data["dmarc_policy"] == "reject"
    assert res.data["gravatar"]["exists"] is True
    assert res.data["gravatar"]["accounts"][0]["site"] == "github"


@respx.mock
async def test_email_profile_free_provider_no_gravatar(monkeypatch):
    async def fake_txt(self, resolver, name, rtype="TXT"):
        return ["5 gmail-smtp-in.l.google.com."] if rtype == "MX" else []

    monkeypatch.setattr(EmailProfileModule, "_txt", fake_txt)
    respx.get(url__startswith="https://en.gravatar.com/").mock(return_value=httpx.Response(404))

    res = await EmailProfileModule().run("someone@gmail.com")
    assert res.data["provider_type"] == "free_webmail"
    assert res.data["gravatar"]["exists"] is False
