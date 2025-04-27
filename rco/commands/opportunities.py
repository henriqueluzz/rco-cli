from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Any, List, Literal, Optional

import typer
from rich.console import Console
from rich.table import Column, Table
from rich.box import SIMPLE
from urllib.parse import quote_plus, urlencode

from rco.utils.requests import JSON_API_ROOT, request_json
from rco.helpers import fmt, fmt_currency, unpack_svelte_payload
from rco.commands.styles import (
    format_operation_strategy,
    style_days_open,
    style_est_profit,
)
from rco.commands.shared import (
    real_profit,
    get_ticker_price_close_price,
    get_ticker_timestamp,
    elapsed_time_since_update
)

from rco.commands.opportunitiesEnums import *


app = typer.Typer(help="List option opportunities with filters")

StatusType = Literal["open", "closed", "exercised"]
OrderType = Literal["asc", "desc"]
SortOptions = Literal[
    "ticker", "strategy", "entry", "current", "profit", "loss",
    "expires", "status", "created", "days_open", "option_ticker",
    "option_strike", "option_type", "profit_50", "profit_100"
]

DEFAULT_STRATEGIES = [
    "venda_de_put_longa",
    "compra_de_call_longa",
    "venda_de_put_mensal",
    "venda_de_put_semanal",
]

console = Console()

@dataclass
class Operation:
    raw: dict[str, Any]

    @property
    def ticker(self) -> str:
        return self.raw["stock"]["ticker"]

    @property
    def entry(self) -> float:
        return float(self.raw.get("entry_price", 0))

    @property
    def current(self) -> float:
        return float(self.raw.get("current_price", 0))

    @property
    def created_at(self) -> date:
        return date.fromisoformat(self.raw["created_at"][:10])

    @property
    def days_open(self) -> int:
        return (date.today() - self.created_at).days

    @property
    def option(self) -> dict[str, Any]:
        return self.raw["operation_legs"][0]["option"]

    @property
    def profit_50(self) -> float:
        return (self.current * 1.5 - self.entry) * 100

    @property
    def profit_100(self) -> float:
        return (self.current * 2.0 - self.entry) * 100

    @property
    def profit(self) -> float:
        return real_profit(
            self.option["type"], self.raw["strategy"], self.entry, self.current
        )

    def to_row(self, last_price: float, last_update: str) -> list[str]:
        return [
            self.ticker,
            format_operation_strategy(self.raw["strategy"]),
            self.option["ticker"],
            fmt_currency(self.entry),
            fmt_currency(self.current),
            f"[{style_est_profit(self.option['type'], self.raw['strategy'], self.current, self.entry)}]{self.profit}[/]",
            fmt(self.raw.get("max_loss")),
            fmt(self.profit_50, "{:.2f}"),
            fmt(self.profit_100, "{:.2f}"),
            self.created_at.isoformat(),
            f"[{style_days_open(self.days_open, 50)}]{self.days_open}[/]",
            fmt_currency(last_price),
            f"{self.option['strike']:.2f}",
            self.option["type"],
            self.raw["expires_at"][:10],
            self.raw["status"],
            last_update,
        ]


@app.command()
def opportunities(
    status: Status = typer.Option(
        Status.open,
        "--status", "-s",
        help="Operation status",
    ),
    strategy: Optional[List[str]] = typer.Option(
        None, "--strategy", "-g",
        help="Filter by strategy (repeatable)"
    ),
    limit: int = typer.Option(
        99, "--limit", "-l",
        max=99,
        help="Max rows to fetch",
    ),
    sort_by: Optional[SortBy] = typer.Option(
        None, "--sort",
        help="Sort by column",
    ),
    order: Order = typer.Option(
        Order.desc, "--order", "-o",
        help="Sort order",
    ),
    ticker: Optional[str] = typer.Option(
        None, "--ticker", "-t",
        help="Filter by ticker (e.g., VALE3)"
    ),
    raw: bool = typer.Option(
        False, "--raw",
        help="Dump raw JSON",
    ),
):
    """
    List option opportunities with optional filters.
    """
    ops = fetch_operations(status, strategy or DEFAULT_STRATEGIES, limit)

    if not ops:
        console.print("[yellow]No results after filters.[/]")
        raise typer.Exit()

    if ticker:
        ops = [op for op in ops if op.ticker == ticker]

    ops = sort_operations(ops, sort_by, order)
    table = build_table(status, ops)
    console.print(table)


def fetch_operations(status: str, strategies: List[str], limit: int) -> list[Operation]:
    params = {"status": status, "limit": str(limit), "strategies": strategies}
    url = JSON_API_ROOT + urlencode(params, quote_via=quote_plus)
    payload = request_json(url)
    ops_raw = unpack_svelte_payload(payload)["operations"]
    return [Operation(op) for op in ops_raw]


def sort_operations(
    operations: list[Operation],
    sort_by: Optional[SortOptions],
    order: OrderType
) -> list[Operation]:
    if not sort_by:
        return operations
    reverse = (order.lower() == "desc")
    return sorted(operations, key=lambda op: getattr(op, sort_by), reverse=reverse)

@lru_cache(maxsize=None)
def get_last_price(ticker: str) -> float:
    return get_ticker_price_close_price(ticker)

@lru_cache(maxsize=None)
def get_last_update(ticker: str) -> str:
    ts = get_ticker_timestamp(ticker)
    return elapsed_time_since_update(ts)


def build_table(status: str, operations: list[Operation]) -> Table:
    table = Table(
        title=f"[bold]Opportunities – {status.upper()} (Total: {len(operations)})[/]",
        box=SIMPLE,
    )
    columns = [
        ("Ticker", "cyan"),
        ("Strategy", "magenta"),
        ("Option", "yellow"),
        ("Entry", None, "right"),
        ("Current", None, "right"),
        ("Real. Profit", None, "right"),
        ("Max Loss", None, "right"),
        ("50% Profit", None, "right"),
        ("100% Profit", None, "right"),
        ("Created", "blue"),
        ("Days Open", None, "right"),
        ("Last Price", None, "right"),
        ("Strike", None, "right"),
        ("Type", "cyan"),
        ("Option Expires", "green"),
        ("Status", "yellow"),
        ("Last Update", "blue"),
    ]
    for header, style, *justify in (
        (col + (None,) * (3 - len(col))) for col in columns
    ):
        table.add_column(header, style=style, justify=justify[0] if justify else None)

    for op in operations:
        last_price = get_last_price(op.ticker)
        last_update = get_last_update(op.ticker)
        table.add_row(*op.to_row(last_price, last_update))

    return table
