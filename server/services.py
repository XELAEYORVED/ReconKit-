"""Shared business logic used by both the API routes and the CLI."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit.models import FAVORITE_TAG, Result, Scan, ScanNote, ScanTag


async def get_scan(session: AsyncSession, scan_id: str) -> Scan | None:
    return (await session.execute(select(Scan).where(Scan.id == scan_id))).scalar_one_or_none()


async def get_scan_dict(session: AsyncSession, scan_id: str,
                        include_results: bool = True) -> dict[str, Any] | None:
    scan = await get_scan(session, scan_id)
    return scan.to_dict(include_results=include_results) if scan else None


async def list_scans(session: AsyncSession, limit: int = 50, offset: int = 0,
                     target: str | None = None, tag: str | None = None,
                     favorite: bool = False) -> list[dict[str, Any]]:
    stmt = select(Scan).order_by(Scan.started_at.desc())
    if target:
        stmt = stmt.where(Scan.target.like(f"%{target}%"))
    if favorite:
        stmt = stmt.where(Scan.tags.any(ScanTag.tag == FAVORITE_TAG))
    if tag:
        stmt = stmt.where(Scan.tags.any(ScanTag.tag == tag))
    stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    return [s.to_dict() for s in rows]


async def add_tag(session: AsyncSession, scan_id: str, tag: str) -> dict[str, Any] | None:
    scan = await get_scan(session, scan_id)
    if not scan:
        return None
    tag = tag.strip().lower()
    if tag and tag not in [t.tag for t in scan.tags]:
        session.add(ScanTag(scan_id=scan_id, tag=tag))
        await session.flush()
        await session.refresh(scan)
    return scan.to_dict()


async def remove_tag(session: AsyncSession, scan_id: str, tag: str) -> dict[str, Any] | None:
    scan = await get_scan(session, scan_id)
    if not scan:
        return None
    for t in list(scan.tags):
        if t.tag == tag.strip().lower():
            await session.delete(t)
    await session.flush()
    await session.refresh(scan)
    return scan.to_dict()


async def toggle_favorite(session: AsyncSession, scan_id: str) -> dict[str, Any] | None:
    scan = await get_scan(session, scan_id)
    if not scan:
        return None
    existing = [t for t in scan.tags if t.tag == FAVORITE_TAG]
    if existing:
        for t in existing:
            await session.delete(t)
    else:
        session.add(ScanTag(scan_id=scan_id, tag=FAVORITE_TAG))
    await session.flush()
    await session.refresh(scan)
    return scan.to_dict()


async def add_note(session: AsyncSession, scan_id: str, content: str) -> dict[str, Any] | None:
    scan = await get_scan(session, scan_id)
    if not scan:
        return None
    note = ScanNote(scan_id=scan_id, content=content.strip())
    session.add(note)
    await session.flush()
    return note.to_dict()


async def delete_note(session: AsyncSession, scan_id: str, note_id: str) -> bool:
    scan = await get_scan(session, scan_id)
    if not scan:
        return False
    for n in list(scan.notes):
        if n.id == note_id:
            await session.delete(n)
            return True
    return False


async def dashboard_stats(session: AsyncSession) -> dict[str, Any]:
    scans = (await session.execute(select(Scan))).scalars().all()
    total = len(scans)
    domains = len({s.target for s in scans})
    threats = sum(1 for s in scans if s.threat_score >= 40)
    by_day: dict[str, int] = {}
    for s in scans:
        if s.started_at:
            day = s.started_at.date().isoformat()
            by_day[day] = by_day.get(day, 0) + 1
    recent = sorted(scans, key=lambda s: s.started_at or s.id, reverse=True)[:10]
    return {
        "total_scans": total,
        "unique_targets": domains,
        "threats_detected": threats,
        "avg_threat_score": round(sum(s.threat_score for s in scans) / total, 1) if total else 0,
        "activity": [{"date": d, "count": c} for d, c in sorted(by_day.items())],
        "recent": [s.to_dict() for s in recent],
    }


def _result_map(scan: Scan) -> dict[str, Result]:
    return {r.module_name: r for r in scan.results}


async def compare_scans(session: AsyncSession, id1: str, id2: str) -> dict[str, Any]:
    s1 = await get_scan(session, id1)
    s2 = await get_scan(session, id2)
    if not s1 or not s2:
        raise ValueError("One or both scans not found")

    m1, m2 = _result_map(s1), _result_map(s2)
    changes: dict[str, dict[str, list]] = {}

    def diff_set(key: str, a: set, b: set) -> None:
        added = sorted(b - a)
        removed = sorted(a - b)
        if added or removed:
            changes[key] = {"added": added, "removed": removed}

    # Subdomains.
    sub1 = set(m1["subdomains"].data.get("subdomains", [])) if "subdomains" in m1 else set()
    sub2 = set(m2["subdomains"].data.get("subdomains", [])) if "subdomains" in m2 else set()
    diff_set("subdomains", sub1, sub2)

    # Open ports (shodan).
    p1 = set(m1["shodan"].data.get("ports", [])) if "shodan" in m1 else set()
    p2 = set(m2["shodan"].data.get("ports", [])) if "shodan" in m2 else set()
    diff_set("open_ports", {str(p) for p in p1}, {str(p) for p in p2})

    # Technologies.
    t1 = set(m1["tech"].data.get("all", [])) if "tech" in m1 else set()
    t2 = set(m2["tech"].data.get("all", [])) if "tech" in m2 else set()
    diff_set("technologies", t1, t2)

    # Emails.
    e1 = set(m1["email"].data.get("emails", [])) if "email" in m1 else set()
    e2 = set(m2["email"].data.get("emails", [])) if "email" in m2 else set()
    diff_set("emails", e1, e2)

    # DNS A records.
    a1 = set(m1["dns"].data.get("ipv4", [])) if "dns" in m1 else set()
    a2 = set(m2["dns"].data.get("ipv4", [])) if "dns" in m2 else set()
    diff_set("ipv4", a1, a2)

    return {
        "scan_before": s1.to_dict(),
        "scan_after": s2.to_dict(),
        "threat_score": {
            "before": s1.threat_score,
            "after": s2.threat_score,
            "delta": s2.threat_score - s1.threat_score,
        },
        "changes": changes,
    }


async def delete_scan(session: AsyncSession, scan_id: str) -> bool:
    scan = await get_scan(session, scan_id)
    if not scan:
        return False
    await session.delete(scan)
    return True
