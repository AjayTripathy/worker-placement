"""
signalos CLI

Commands:
    run     --zip 48238 [--deeds] [--llm] [--db signalos.db]
    report  [--zip 48238] [--tier high|medium|low|exempt] [--csv out.csv]
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from core.engine import SignalEngine
from core.models import Entity
from store.sqlite import SQLiteSignalStore
from verticals.property_tax.jurisdictions.detroit import assessor as assessor_src
from verticals.property_tax.jurisdictions.detroit.config import DETROIT_ZIP_CODES
from verticals.property_tax.jurisdictions.detroit.registry import build_engine

from .report import print_summary, print_table, export_csv

console = Console()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--zip", "zip_codes", help="Comma-separated zip codes (default: all Detroit)")
@click.option("--parcel", help="Single parcel ID")
@click.option("--deeds", is_flag=True, help="Include Wayne County deed scraper (~15s/parcel)")
@click.option("--mls", "include_mls", is_flag=True, help="Fetch Zillow/Redfin sale history (slow — use on small parcel sets)")
@click.option("--llm", "use_llm", is_flag=True, help="Enable LLM fallback for PA210/OPRA rules")
@click.option("--db", default="signalos.db", show_default=True, help="SQLite database path")
def run(zip_codes, parcel, deeds, include_mls, use_llm, db):
    """Fetch assessor data and compute property tax signals."""
    store = SQLiteSignalStore(db)
    engine = build_engine(include_deeds=deeds, include_mls=include_mls, use_llm=use_llm)
    engine.store = store

    if parcel:
        parcel_id = parcel.strip().rstrip(".")
        seed = assessor_src.fetch(parcel_id)
        address = seed[0].data.get("address", "") if seed else ""
        entity = Entity(
            id=parcel_id,
            entity_type="parcel",
            vertical="property_tax",
            jurisdiction="detroit",
            metadata={"address": address},
        )
        signal = engine.run_one(entity, seed_records=seed)
        if signal:
            console.print(f"[green]Signal computed:[/] score={signal.fraud_score} tier={signal.fraud_tier}")
            console.print(f"  net_gap=${float(signal.net_gap):,.0f}  impact=${float(signal.estimated_annual_impact or 0):,.0f}/yr")
        else:
            console.print("[dim]No gap detected for this parcel.[/dim]")
        return

    zips = [z.strip() for z in zip_codes.split(",")] if zip_codes else DETROIT_ZIP_CODES

    total_processed = 0
    total_signaled = 0

    for zc in zips:
        console.print(f"[bold]Processing zip {zc}...[/bold]")
        records_iter = assessor_src.fetch_zip(zc)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"zip {zc}", total=None)

            for record in records_iter:
                entity = Entity(
                    id=record.entity_id,
                    entity_type="parcel",
                    vertical="property_tax",
                    jurisdiction="detroit",
                    metadata={
                        "address": record.data.get("address", ""),
                        "zip_code": zc,
                    },
                )
                # Pass the already-fetched assessment record as seed so the engine
                # skips re-fetching it and only calls the MLS sources (Zillow/Redfin).
                signal = engine.run_one(entity, seed_records=[record])
                total_processed += 1
                if signal:
                    total_signaled += 1
                progress.advance(task)

    console.print(f"\n[green]Done.[/green] {total_processed} parcels processed, {total_signaled} signals written.")


@cli.command()
@click.option("--zip", "zip_code", help="Filter by zip code")
@click.option("--tier", type=click.Choice(["high", "medium", "low", "exempt"]), help="Filter by fraud tier")
@click.option("--min-score", type=int, default=0, help="Minimum fraud score")
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--csv", "csv_path", help="Export all results to CSV")
@click.option("--db", default="signalos.db", show_default=True)
def report(zip_code, tier, min_score, limit, csv_path, db):
    """Print signal report."""
    store = SQLiteSignalStore(db)
    filters = {}
    if zip_code:
        filters["jurisdiction"] = "detroit"
    rows = store.read_signals(**filters)

    if tier:
        rows = [r for r in rows if r["fraud_tier"] == tier]
    if min_score:
        rows = [r for r in rows if r["fraud_score"] >= min_score]

    if not rows:
        console.print("[yellow]No signals found. Run `signalos run` first.[/yellow]")
        sys.exit(0)

    print_summary(rows)
    print_table(rows, limit=limit)

    if csv_path:
        export_csv(rows, csv_path)
