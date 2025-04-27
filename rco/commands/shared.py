from rco.utils.requests import API_ROOT, request_json
from datetime import datetime, timedelta


def get_ticker_price_close_price(ticker: str, field: str = "close") -> float:
    """
    Fetch the last quoted value of *field* for a stock ticker.
    Default field is 'close'.
    """
    params = f"fields={field}"
    uri = f"{API_ROOT}/assets/{ticker}?{params}"
    return request_json(uri)[field]


def get_ticker_variability(ticker: str, field: str = "variacao") -> str:
    params = f"fields={field}"
    uri = f"{API_ROOT}/assets/{ticker}?{params}"

    return request_json(uri)[field]


def get_ticker_timestamp(ticker: str, field: str = "timestamp") -> str:
    params = f"fields={field}"
    uri = f"{API_ROOT}/assets/{ticker}?{params}"

    return request_json(uri)[field]


def elapsed_time_since_update(timestamp: str, supress_seconds: bool = True) -> str:
    last_update = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    now = datetime.now()
    elapsed = now - last_update

    if elapsed.days > 0:
        return f"{elapsed.days} day(s) ago"

    hours, remainder = divmod(elapsed.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    if hours:
        parts.append(f"{hours}h")

    if minutes:
        parts.append(f"{minutes}m")

    if (seconds or not parts) and not supress_seconds:
        parts.append(f"{seconds} second(s)")

    return ":".join(parts) + " ago"


def real_profit(option: str, strategy: str, entry: float, current: float):
    if "venda" in strategy and option == "put":
        return entry - current

    if "compra" in strategy and option == "call":
        return current - entry
    
    else:
        return -0.0

