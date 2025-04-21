from __future__ import annotations

import typer
from typing import Optional

from rco.commands.opportunities import opportunities_cmd
from rco.commands.price import price_cmd 

app = typer.Typer(
    add_help_option=False,
    no_args_is_help=True,
    help="RendacomOpcoes CLI.  Use `rco <command> --help` for details.",
)

app.command(name="opportunities")(opportunities_cmd)
app.command(name="price")(price_cmd) 

# top‑level help / default behaviour
@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context,
          help: Optional[bool] = typer.Option(None, "-h", "--help")):
    if help or ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

if __name__ == "__main__":
    app()
