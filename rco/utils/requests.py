import requests
import typer
import json
import os
import sys
import warnings

API_ROOT = "https://app.rendacomopcoes.com.br/api"
JSON_API_ROOT = "https://app.rendacomopcoes.com.br/opportunities/__data.json?"

warnings.filterwarnings("ignore", category=Warning, module="urllib3")

def get_cookie() -> str:
    cookie = os.getenv("COOKIE_JAR")
    if not cookie:
        typer.secho(
            "❌ COOKIE_JAR environment variable is not set.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    return cookie

def request_json(url: str) -> dict:
    cookie = get_cookie()
    headers = {"Accept": "*/*"}
    resp = requests.get(f"{url}", headers=headers, cookies=dict([c.split('=', 1) for c in cookie.split('; ')]))
    resp.raise_for_status()
    return resp.json()
