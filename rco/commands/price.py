from __future__ import annotations

from statistics import mean
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from rco.utils.requests import API_ROOT, request_json
from rco.commands.shared import get_ticker_price_close_price 

console = Console()


def price_cmd(                       
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g., VALE3)"),
    avg: int = typer.Option(
        None, "--avg", "-a", help="Show the arithmetic mean of the last N days"
    ),
    raw: bool = typer.Option(False, "--raw", help="Print raw JSON instead"),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress table; print only the average"
    ),
) -> None:
    """
    Show daily closing prices for a TICKER.

    Examples:
        rco price VALE3
        rco price VALE3 --avg 5
        rco price VALE3 --avg 10 --quiet
    """
    data = request_json(f"{API_ROOT}/assets/{ticker}/history")
    dates = data.get("dates", [])
    if not dates:
        console.print(f"[yellow]No price data returned for {ticker}[/]")
        raise typer.Exit()

    dates.sort(key=lambda d: d["date"], reverse=True)

    avg_val: Optional[float] = None
    if avg:
        subset = dates[:avg]
        avg_val = mean(d["price"] for d in subset)

    if quiet and avg:
        typer.echo(f"{avg_val:.4f}")
        raise typer.Exit()

    if raw:
        console.print_json(data=data)
        if avg:
            console.print(f"[bright_black]Average ({len(subset)} day): "
                          f"{avg_val:.4f}[/]")
        return

    table = Table(title=f"[bold]Price history – {ticker}[/]", box=box.SIMPLE)
    table.add_column("Date", style="cyan")
    table.add_column("Close", justify="right", style="green")
    for d in dates[:30]:
        table.add_row(d["date"], f"{d['price']:.2f}")

    console.print(table)
    if avg:
        console.print(f"[bold bright_black]{len(subset)}‑day average "
                      f"{avg_val:.2f}[/]")
