from __future__ import annotations

import json
import os
import sys
import textwrap
from datetime import date
from functools import lru_cache
from statistics import mean
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode

import requests
import typer
import warnings
from rich import box, print
from rich.console import Console
from rich.table import Table

from rco.utils.requests import API_ROOT, JSON_API_ROOT, get_cookie, request_json
from rco.helpers import *

app = typer.Typer(add_help_option=False, no_args_is_help=True)
console = Console()

warnings.filterwarnings("ignore", category=Warning, module="urllib3")

@app.command(name="opportunities")
def opportunities_cmd(
    status: str = typer.Option(
        "open",
        "--status",
        "-s",
        help="Operation status (open, closed, exercised)"
    ),
    strategy: List[str] = typer.Option(
        None,
        "--strategy",
        "-g",
        help="Filter by strategy (repeatable)"
    ),
    limit: int = typer.Option(
        99,
        "--limit",
        "-l",
        help="Max rows to fetch from the API (<= 99)"
    ),
    sort: str = typer.Option(
        None,
        "--sort",
        help="Sort by column (id, ticker, strategy, entry, current, profit, loss, profit_max, expires, status, created, days_open, option_ticker, option_strike, option_type, option_expires, profit_50, profit_100)"
    ),
    order: str = typer.Option(
        "desc",
        "--order",
        "-o",
        help="Sort order (asc, desc)"
    ),
    filter_ticker: str = typer.Option(
        None,
        "--filter-ticker",
        "-t",
        help="Filter by ticker (e.g., VALE3)"
    ),
    filter_strategy: str = typer.Option(
        None,
        "--filter-strategy",
        "-f",
        help="Filter by strategy (e.g., venda_de_put_semanal)"
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Dump raw JSON instead of a table"
    ),
) -> None:
    """
    List option **opportunities** with optional filters.

    Examples
    --------
    • rco opportunities                                    # open ops, any strategy  
    • rco opportunities -s exercised                       # only exercised  
    • rco opportunities -g venda_de_put_semanal -s closed  # filter by strategy + status
    • rco opportunities --sort profit                      # sort by estimated profit
    • rco opportunities --sort profit -o asc               # sort by estimated profit ascending
    • rco opportunities -t VALE3                           # filter by ticker
    • rco opportunities -f venda_de_put_semanal            # filter by strategy
    """

    params: dict[str, Any] = {
        "strategies": [
            "venda_de_put_longa",
            "compra_de_call_longa", 
            "venda_de_put_mensal",
            "venda_de_put_semanal"
        ],
        "status": status,
        "limit": "99"
    }

    if strategy:
        params["filters"] = json.dumps({"strategies": strategy})

    url = JSON_API_ROOT + urlencode(params, quote_via=quote_plus)
    data = request_json(url)

    if raw:
        console.print_json(data=data)
        raise typer.Exit()

    parsedSvelte = unpack_svelte_payload(data)
    operations = parsedSvelte["operations"]
    if not operations:
        console.print("[bold yellow]No results returned.[/]")
        raise typer.Exit()

    if filter_ticker:
        operations = [op for op in operations if op["stock"]["ticker"] == filter_ticker]
    if filter_strategy:
        operations = [op for op in operations if op["strategy"] == filter_strategy]

    if not operations:
        console.print("[bold yellow]No results match the specified filters.[/]")
        raise typer.Exit()

    # Sort operations if sort parameter is provided
    if sort:
        sort_mapping = {
            "id": lambda op: op["id"],
            "ticker": lambda op: op["stock"]["ticker"],
            "strategy": lambda op: op["strategy"],
            "entry": lambda op: op.get("entry_price", 0),
            "current": lambda op: op.get("current_price", 0),
            "profit": lambda op: op.get("estimated_profit", 0),
            "loss": lambda op: op.get("max_loss", 0),
            "expires": lambda op: op["expires_at"],
            "status": lambda op: op["status"],
            "created": lambda op: op["created_at"],
            "days_open": lambda op: (date.today() - date.fromisoformat(op["created_at"].split("T")[0])).days,
            "option_ticker": lambda op: op["operation_legs"][0]["option"]["ticker"],
            "option_strike": lambda op: op["operation_legs"][0]["option"]["strike"],
            "option_type": lambda op: op["operation_legs"][0]["option"]["type"],
            "profit_50": lambda op: (op.get("current_price", 0) * 1.5 - op.get("entry_price", 0)) * 100,
            "profit_100": lambda op: (op.get("current_price", 0) * 2 - op.get("entry_price", 0)) * 100
        }
        
        if sort not in sort_mapping:
            console.print(f"[bold red]Invalid sort column: {sort}[/]")
            console.print("Valid columns: " + ", ".join(sort_mapping.keys()))
            raise typer.Exit(1)
            
        if order not in ["asc", "desc"]:
            console.print(f"[bold red]Invalid sort order: {order}[/]")
            console.print("Valid orders: asc, desc")
            raise typer.Exit(1)
            
        operations.sort(key=sort_mapping[sort], reverse=(order == "desc"))

    # ------------------------------------------------------------------ output
    table = Table(
        title=f"[bold]Opportunities – {status.upper()} (Total: {len(operations)})[/]", 
        box=box.SIMPLE
    )
    table.add_column("ID", justify="right")
    table.add_column("Ticker", style="cyan")
    table.add_column("Strategy", style="magenta")
    table.add_column("Entry", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Est. Profit", justify="right")
    table.add_column("Max Loss", justify="right")
    table.add_column("50% Profit", justify="right")
    table.add_column("100% Profit", justify="right")
    table.add_column("Expires", style="green")
    table.add_column("Created", style="blue")
    table.add_column("Days Open", justify="right")
    table.add_column("Option", style="yellow")
    table.add_column("Last Price", justify="right")
    table.add_column("Strike", justify="right")
    table.add_column("Type", style="cyan")
    table.add_column("Option Expires", style="green")
    table.add_column("Status", style="yellow")

    for op in operations:
        stock = op["stock"]
        created_date = date.fromisoformat(op["created_at"].split("T")[0])
        days_open = (date.today() - created_date).days
        option = op["operation_legs"][0]["option"]
        
        # Calculate potential profits
        current_price = op.get("current_price", 0)
        entry_price = op.get("entry_price", 0)
        profit_50 = (current_price * 1.5 - entry_price) * 100
        profit_100 = (current_price * 2 - entry_price) * 100
        
        table.add_row(
            str(op["id"]),
            stock["ticker"],
            op["strategy"],
            fmt(op.get("entry_price"), "{:.3f}"),
            fmt(op.get("current_price"), "{:.3f}"),
            fmt(op.get("estimated_profit")),
            fmt(op.get("max_loss")),
            fmt(profit_50, "{:.2f}"),
            fmt(profit_100, "{:.2f}"),
            op["expires_at"].split("T")[0],
            op["created_at"].split("T")[0],
            str(days_open),
            option["ticker"],
            fmt(get_ticker_price_close_price(stock["ticker"]), "{:.3f}"),
            f'{option["strike"]:.2f}',
            option["type"],
            option["expires_at"].split("T")[0],
            op["status"]
        )

    console.print(table)

@app.command()
def price(
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g., VALE3)"),
    avg: int = typer.Option(None, "--avg", "-a",
                            help="Show the arithmetic mean of the last N days"),
    raw: bool = typer.Option(False, "--raw", help="Print raw JSON instead of table"),
    quiet: bool = typer.Option(False, "--quiet", "-q",
                               help="Suppress table; print only the average value"),
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
        console.print(f"[bold yellow]No price data returned for {ticker}[/]")
        raise typer.Exit()

    # Sort newest‑first just in case the API isn't already
    dates.sort(key=lambda d: d["date"], reverse=True)

    avg_value = None
    if avg:
        if len(dates) < avg:
            console.print(f"[yellow]Only {len(dates)} day(s) available; "
                          f"computing average on those[/]")
        subset = dates[:avg]
        avg_value = mean(d["price"] for d in subset)

    # If the user only wants the number, print & exit early
    if quiet and avg:
        typer.echo(f"{avg_value:.4f}")
        raise typer.Exit()

    if raw:
        console.print_json(data=data)
        if avg:
            console.print(f"[bright_black]Average of last {len(subset)} "
                          f"day(s): {avg_value:.4f}[/]")
        return

    # Pretty table
    table = Table(title=f"[bold]Price history – {ticker}[/]", box=box.SIMPLE)
    table.add_column("Date", style="cyan")
    table.add_column("Close", justify="right", style="green")

    for d in dates[:30]:           
        table.add_row(d["date"], f"{d['price']:.2f}")

    console.print(table)

    if avg:
        console.print(f"[bold bright_black]{len(subset)}‑day average "
                      f"{avg_value:.2f}[/]")


def get_ticker_price_close_price(ticker: str, field:str = "close") -> dict:
    params = f"fields={field}"
    uri = f"{API_ROOT}/assets/{ticker}?{params}"

    return request_json(uri)[field]


@app.callback(invoke_without_command=True)
def _(ctx: typer.Context, help: Optional[bool] = typer.Option(None, "-h", "--help")):
    """
    RendacomOpcoes CLI.

    Use [bold]rco <command> --help[/] for details.
    """
    if help:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
