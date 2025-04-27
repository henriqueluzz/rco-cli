from enum import Enum

class Status(str, Enum):
    open = "open"
    closed = "closed"
    exercised = "exercised"

class Order(str, Enum):
    asc = "asc"
    desc = "desc"

class SortBy(str, Enum):
    ticker          = "ticker"
    strategy        = "strategy"
    entry           = "entry"
    current         = "current"
    profit          = "profit"
    loss            = "loss"
    expires         = "expires"
    status          = "status"
    created         = "created"
    days_open       = "days_open"
    option_ticker   = "option_ticker"
    option_strike   = "option_strike"
    option_type     = "option_type"
    profit_50       = "profit_50"
    profit_100      = "profit_100"
