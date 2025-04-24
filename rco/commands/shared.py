from rco.utils.requests import API_ROOT, request_json


def get_ticker_price_close_price(ticker: str, field: str = "close") -> float:
    """
    Fetch the last quoted value of *field* for a stock ticker.
    Default field is 'close'.
    """
    params = f"fields={field}"
    uri = f"{API_ROOT}/assets/{ticker}?{params}"
    return request_json(uri)[field]


def get_ticker_variability(ticker: str, field: str = "variacao") -> dict:
    params = f"fields={field}"
    uri = f"assets/{ticker}?{params}"

    return request_json(uri)[field]


def get_ticker_timestamp(ticker: str, field: str = "timestamp") -> dict:
    params = f"fields={field}"
    uri = f"assets/{ticker}?{params}"

    return request_json(uri)[field]