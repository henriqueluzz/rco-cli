from __future__ import annotations

import json
from datetime import date
from statistics import mean
from typing import Any, List, Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from urllib.parse import urlencode, quote_plus  
from rco.utils.requests import JSON_API_ROOT, request_json
from rco.helpers import fmt, unpack_svelte_payload
from rco.commands.shared import get_ticker_price_close_price

console = Console()

def opportunities_cmd(               
    status: str = typer.Option(
        "open", "--status", "-s",
        help="Operation status (open, closed, exercised)"
    ),
    strategy: List[str] = typer.Option(
        None, "--strategy", "-g", help="Filter by strategy (repeatable)"
    ),
    limit: int = typer.Option(
        99, "--limit", "-l",
        help="Max rows to fetch from the API (<= 99)"
    ),
    sort: str = typer.Option(
        None, "--sort",
        help=("Sort by column (id, ticker, strategy, entry, current, profit, "
              "loss, profit_max, expires, status, created, days_open, "
              "option_ticker, option_strike, option_type, option_expires, "
              "profit_50, profit_100)")
    ),
    order: str = typer.Option("desc", "--order", "-o",
                              help="Sort order (asc, desc)"),
    filter_ticker: str = typer.Option(
        None, "--filter-ticker", "-t", help="Filter by ticker (e.g., VALE3)"
    ),
    filter_strategy: str = typer.Option(
        None, "--filter-strategy", "-f",
        help="Filter by strategy (e.g., venda_de_put_semanal)"
    ),
    raw: bool = typer.Option(False, "--raw", help="Dump raw JSON"),
) -> None:
    """
    List option **opportunities** with optional filters.
    """
    # ---------------------------------------------------------------- params → API
    params: dict[str, Any] = {
        "strategies": [
            "venda_de_put_longa",
            "compra_de_call_longa",
            "venda_de_put_mensal",
            "venda_de_put_semanal",
        ],
        "status": status,
        "limit": str(limit),
    }
    if strategy:
        params["filters"] = json.dumps({"strategies": strategy})

    url = JSON_API_ROOT + urlencode(params, quote_via=quote_plus)
    data = request_json(url)
    if raw:
        console.print_json(data=data)
        raise typer.Exit()

    # --------------------------------------------------------------- filtering
    ops = unpack_svelte_payload(data)["operations"]
    if filter_ticker:
        ops = [o for o in ops if o["stock"]["ticker"] == filter_ticker]
    if filter_strategy:
        ops = [o for o in ops if o["strategy"] == filter_strategy]
    if not ops:
        console.print("[yellow]No results after filters.[/]")
        raise typer.Exit()

    sort_map = {
        "id": lambda o: o["id"],
        "ticker": lambda o: o["stock"]["ticker"],
        "strategy": lambda o: o["strategy"],
        "entry": lambda o: o.get("entry_price", 0),
        "current": lambda o: o.get("current_price", 0),
        "profit": lambda o: o.get("estimated_profit", 0),
        "loss": lambda o: o.get("max_loss", 0),
        "expires": lambda o: o["expires_at"],
        "status": lambda o: o["status"],
        "created": lambda o: o["created_at"],
        "days_open": lambda o: (
            date.today() - date.fromisoformat(o["created_at"].split("T")[0])
        ).days,
        "option_ticker": lambda o: o["operation_legs"][0]["option"]["ticker"],
        "option_strike": lambda o: o["operation_legs"][0]["option"]["strike"],
        "option_type": lambda o: o["operation_legs"][0]["option"]["type"],
        "profit_50": lambda o: (o.get("current_price", 0) * 1.5
                                - o.get("entry_price", 0)) * 100,
        "profit_100": lambda o: (o.get("current_price", 0) * 2
                                 - o.get("entry_price", 0)) * 100,
    }
    if sort:
        if sort not in sort_map:
            console.print(f"[red]Invalid sort column:[/] {sort}")
            raise typer.Exit(1)
        ops.sort(key=sort_map[sort], reverse=(order == "desc"))

    table = Table(
        title=f"[bold]Opportunities – {status.upper()} (Total: {len(ops)})[/]",
        box=box.SIMPLE,
    )
    table.add_column("ID",          justify="right")
    table.add_column("Ticker",      style="cyan")
    table.add_column("Strategy",    style="magenta")
    table.add_column("Entry",       justify="right")
    table.add_column("Current",     justify="right")
    table.add_column("Est. Profit", justify="right")
    table.add_column("Max Loss",    justify="right")
    table.add_column("50% Profit",  justify="right")
    table.add_column("100% Profit", justify="right")
    table.add_column("Expires",     style="green")
    table.add_column("Created",     style="blue")
    table.add_column("Days Open",   justify="right")
    table.add_column("Option",      style="yellow")
    table.add_column("Last Price",  justify="right")
    table.add_column("Strike",      justify="right")
    table.add_column("Type",        style="cyan")
    table.add_column("Option Expires", style="green")
    table.add_column("Status",      style="yellow")

    for op in ops:
        stock = op["stock"]
        created = date.fromisoformat(op["created_at"].split("T")[0])
        days_open = (date.today() - created).days
        option = op["operation_legs"][0]["option"]
        cur = op.get("current_price", 0)
        ent = op.get("entry_price", 0)
        profit_50 = (cur * 1.5 - ent) * 100
        profit_100 = (cur * 2 - ent) * 100

        table.add_row(
            str(op["id"]),
            stock["ticker"],
            op["strategy"],
            fmt(ent, "{:.3f}"),
            fmt(cur, "{:.3f}"),
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
            op["status"],
        )

    console.print(table)
