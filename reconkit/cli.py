"""ReconKit command-line interface (Click)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table

from . import ETHICAL_BANNER, __version__
from .database import init_db, session_scope
from .engine import ReconEngine
from .models import TargetType
from .modules import get_registry

console = Console()


def banner() -> None:
    console.print(Panel(ETHICAL_BANNER, title=f"ReconKit v{__version__}",
                        border_style="green", expand=False))


def _run(coro):
    return asyncio.run(coro)


@click.group()
@click.version_option(__version__, prog_name="reconkit")
def cli() -> None:
    """ReconKit — passive OSINT reconnaissance toolkit."""


@cli.command()
@click.argument("target")
@click.option("--modules", "-m", default=None, help="Comma-separated module names (default: auto).")
@click.option("--type", "target_type", type=click.Choice([t.value for t in TargetType]),
              default=None, help="Force target type instead of auto-detection.")
@click.option("--concurrency", "-c", default=None, type=int, help="Max concurrent modules.")
@click.option("--timeout", "-t", default=None, type=int, help="Per-module timeout (seconds).")
@click.option("--output", "-o", type=click.Path(), default=None, help="Write JSON report to file.")
@click.option("--no-save", is_flag=True, help="Do not persist to the database.")
def scan(target, modules, target_type, concurrency, timeout, output, no_save):
    """Run a passive scan against TARGET (domain, IP, email or username)."""
    banner()
    mods = [m.strip() for m in modules.split(",")] if modules else None
    tt = TargetType(target_type) if target_type else None

    async def _go():
        await init_db()
        progress = Progress(
            TextColumn("[cyan]{task.description}"), BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"), TimeElapsedColumn(), console=console,
        )
        task_id = progress.add_task("scanning", total=1.0)
        statuses: dict[str, str] = {}

        async def cb(event):
            ev = event.get("event")
            if ev == "scan_start":
                for m in event["modules"]:
                    statuses[m] = "pending"
                progress.update(task_id, description=f"{target} ({event['target_type']})")
            elif ev == "module_start":
                statuses[event["module"]] = "running"
            elif ev in ("module_complete", "module_error"):
                statuses[event["module"]] = event.get("status", "done")
                progress.update(task_id, completed=event.get("progress", 0))
            elif ev == "scan_complete":
                progress.update(task_id, completed=1.0)

        eng = ReconEngine(progress_cb=cb)
        with progress:
            result = await eng.run_scan(
                target, modules=mods, target_type=tt,
                max_concurrency=concurrency, timeout=timeout, persist=not no_save,
            )
        return result, statuses

    try:
        result, statuses = _run(_go())
    except Exception as exc:
        console.print(f"[red]Scan failed:[/red] {exc}")
        sys.exit(1)

    _print_summary(result, statuses)
    if output:
        from .report import render_json
        Path(output).write_text(render_json(result), encoding="utf-8")
        console.print(f"[green]JSON report written to[/green] {output}")
    if not no_save:
        console.print(f"\n[green]Saved scan:[/green] [bold]{result['scan_id']}[/bold]")


def _print_summary(result, statuses):
    s = result["summary"]
    risk = s.get("risk_level", "low")
    color = {"critical": "red", "high": "orange3", "medium": "yellow", "low": "green"}[risk]
    console.print(
        Panel(f"[bold {color}]Threat Score: {result['threat_score']}/100 "
              f"({risk.upper()})[/bold {color}]", border_style=color, expand=False))

    tbl = Table(title="Modules", show_lines=False)
    tbl.add_column("Module"); tbl.add_column("Status"); tbl.add_column("Summary")
    icons = {"ok": "[green]OK[/green]", "error": "[red]ERR[/red]",
             "skipped": "[yellow]SKIP[/yellow]", "running": "[cyan]..[/cyan]"}
    for r in result["results"]:
        st = icons.get(r["status"], r["status"])
        summary = _module_oneliner(r)
        tbl.add_row(r["module_name"], st, summary)
    console.print(tbl)

    factors = s.get("threat_factors", [])
    if factors:
        ftbl = Table(title="Threat Factors")
        ftbl.add_column("Pts", justify="right"); ftbl.add_column("Reason")
        for f in factors:
            ftbl.add_row(f"+{f['points']}", f["reason"])
        console.print(ftbl)


def _module_oneliner(r) -> str:
    if r["status"] != "ok":
        return f"[dim]{r.get('error', '')}[/dim]"
    d = r["data"]
    n = r["module_name"]
    if n == "dns":
        return f"{len(d.get('records', {}))} record types, {len(d.get('ipv4', []))} IPv4"
    if n == "subdomains":
        return f"{d.get('count', 0)} subdomains ({d.get('live_count', 0)} live)"
    if n == "cert_transparency":
        return f"{d.get('unique_certificates', 0)} certs, {d.get('san_count', 0)} SANs"
    if n == "tech":
        return ", ".join(d.get("all", [])[:5]) or "none detected"
    if n == "headers":
        return f"grade {d.get('grade')} ({d.get('score')}/100)"
    if n == "shodan":
        return f"ports {d.get('ports', [])}, {len(d.get('vulns', []))} CVEs"
    if n == "ip_geo":
        return f"{d.get('ip')} — {d.get('city')}, {d.get('country')} ({d.get('asn')})"
    if n == "email":
        return f"{d.get('email_count', 0)} emails"
    if n == "social":
        return f"{d.get('found_count', 0)}/{d.get('checked', 0)} platforms"
    if n == "leak_check":
        return f"{d.get('breach_count', 0)} breaches" if d.get("breached") else "no breaches"
    if n == "wayback":
        return f"{d.get('snapshot_count', 0)} snapshots"
    return f"{len(d)} fields"


@cli.command()
@click.argument("scan_id1")
@click.argument("scan_id2")
def compare(scan_id1, scan_id2):
    """Diff two scans of the same target."""
    from server.services import compare_scans  # reuse service

    async def _go():
        await init_db()
        async with session_scope() as session:
            return await compare_scans(session, scan_id1, scan_id2)

    try:
        diff = _run(_go())
    except Exception as exc:
        console.print(f"[red]Compare failed:[/red] {exc}")
        sys.exit(1)

    console.print(Panel(f"Comparing [bold]{scan_id1}[/bold] -> [bold]{scan_id2}[/bold]",
                        border_style="cyan"))
    console.print(f"Threat score: {diff['threat_score']['before']} -> "
                  f"{diff['threat_score']['after']} ({diff['threat_score']['delta']:+d})")
    for key, change in diff["changes"].items():
        if change.get("added") or change.get("removed"):
            console.print(f"\n[bold]{key}[/bold]")
            for a in change.get("added", []):
                console.print(f"  [green]+ {a}[/green]")
            for r in change.get("removed", []):
                console.print(f"  [red]- {r}[/red]")


@cli.command()
@click.argument("scan_id")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["json", "md", "markdown", "html", "pdf", "csv", "stix", "misp"]),
              default="json")
@click.option("--output", "-o", type=click.Path(), default=None)
def export(scan_id, fmt, output):
    """Export a saved scan to a report or threat-intel format."""
    from sqlalchemy import select

    from . import export as exporter
    from . import report as reporter
    from .models import Scan

    async def _go():
        await init_db()
        async with session_scope() as session:
            scan = (await session.execute(
                select(Scan).where(Scan.id == scan_id))).scalar_one_or_none()
            if not scan:
                raise click.ClickException(f"Scan {scan_id} not found")
            return scan.to_dict(include_results=True)

    data = _run(_go())
    if fmt in ("json", "md", "markdown", "html", "pdf"):
        content, _ = reporter.render(data, fmt)
    else:
        content, _ = exporter.export(data, fmt)

    ext = {"markdown": "md"}.get(fmt, fmt)
    out = output or f"{scan_id}.{ext}"
    Path(out).write_bytes(content)
    console.print(f"[green]Exported[/green] {scan_id} -> {out} ({fmt})")


@cli.command("list")
@click.option("--limit", "-n", default=20)
def list_scans(limit):
    """List saved scans."""
    from sqlalchemy import select

    from .models import Scan

    async def _go():
        await init_db()
        async with session_scope() as session:
            rows = (await session.execute(
                select(Scan).order_by(Scan.started_at.desc()).limit(limit))).scalars().all()
            return [s.to_dict() for s in rows]

    scans = _run(_go())
    tbl = Table(title="Scans")
    for col in ("ID", "Target", "Type", "Status", "Score", "Started"):
        tbl.add_column(col)
    for s in scans:
        tbl.add_row(s["id"], s["target"], s["target_type"] or "",
                    s["status"] or "", str(s["threat_score"]), (s["started_at"] or "")[:19])
    console.print(tbl)


@cli.command()
def modules():
    """List all available recon modules."""
    banner()
    reg = get_registry()
    tbl = Table(title=f"{len(reg)} passive modules")
    for col in ("Name", "Category", "Types", "API key", "Description"):
        tbl.add_column(col, overflow="fold")
    for name in sorted(reg):
        m = reg[name]()
        tbl.add_row(
            name, m.category,
            ",".join(t.value for t in m.supported_types),
            "required" if m.requires_api_key else ("optional" if m.api_service else "no"),
            m.description,
        )
    console.print(tbl)


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000, type=int)
@click.option("--reload", is_flag=True)
def serve(host, port, reload):
    """Launch the ReconKit web server (FastAPI + WebSocket)."""
    banner()
    import uvicorn
    console.print(f"[green]Starting server at[/green] http://{host}:{port}")
    uvicorn.run("server.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    cli()
