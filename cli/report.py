from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

console = Console()

TIER_STYLE = {"high": "bold red", "medium": "bold yellow", "low": "dim", "exempt": "dim green"}


def _fmt(v) -> str:
    if v is None:
        return "—"
    return f"${float(v):,.0f}"


def print_summary(rows: list[dict]):
    counts = {}
    total_impact = Decimal(0)
    for r in rows:
        counts[r["fraud_tier"]] = counts.get(r["fraud_tier"], 0) + 1
        if r.get("estimated_annual_impact"):
            total_impact += Decimal(str(r["estimated_annual_impact"]))

    console.print(f"\n[bold]Property Tax Signal Report[/bold]  ({len(rows)} signals)\n")
    console.print(f"  [bold red]High:[/]    {counts.get('high', 0):>6}")
    console.print(f"  [bold yellow]Medium:[/]  {counts.get('medium', 0):>6}")
    console.print(f"  [dim]Low:[/]     {counts.get('low', 0):>6}")
    console.print(f"  [dim green]Exempt:[/]  {counts.get('exempt', 0):>6}")
    console.print(f"\n  Estimated annual impact: [bold]{_fmt(total_impact)}[/bold]\n")


def print_table(rows: list[dict], limit: int = 50):
    t = Table(box=box.SIMPLE_HEAVY, show_lines=False)
    t.add_column("Tier",      width=8)
    t.add_column("Score",     justify="right", width=6)
    t.add_column("Entity",    width=14)
    t.add_column("Direction", width=14)
    t.add_column("Raw Gap",   justify="right")
    t.add_column("Net Gap",   justify="right")
    t.add_column("Impact/yr", justify="right", style="bold")
    t.add_column("Method",    width=10)
    t.add_column("Quality",   width=14)

    for r in rows[:limit]:
        meta = json.loads(r.get("gap_metadata") or "{}")
        tier = r["fraud_tier"]
        style = TIER_STYLE.get(tier, "")
        score = r["fraud_score"]
        score_cell = f"[{style}]{score}[/]" if score else "—"

        t.add_row(
            f"[{style}]{tier.upper()}[/]",
            score_cell,
            r["entity_id"][:14],
            r.get("gap_direction") or "—",
            _fmt(r.get("raw_gap")),
            _fmt(r.get("net_gap")),
            _fmt(r.get("estimated_annual_impact")),
            meta.get("method_agreement") or "—",
            meta.get("data_quality") or "—",
        )

    console.print(t)
    if len(rows) > limit:
        console.print(f"[dim]...and {len(rows) - limit} more. Use --csv to export all.[/dim]\n")


def export_csv(rows: list[dict], path: str | Path):
    path = Path(path)
    if not rows:
        console.print("[yellow]No rows to export.[/yellow]")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    console.print(f"[green]Exported {len(rows)} rows → {path}[/green]")
