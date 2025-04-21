# RCO CLI

A command-line interface for RendacomOpcoes, a Brazilian options trading platform.

## Installation

```bash
pip install rco-cli
```

## Environment Variables

The CLI requires a `COOKIE_JAR` environment variable to be set with your session cookie from RendacomOpcoes:

```bash
export COOKIE_JAR="your_cookie_here"
```

## Commands

### Opportunities

List option opportunities with various filters and sorting options.

```bash
# List all open opportunities
rco opportunities

# List only exercised opportunities
rco opportunities -s exercised

# Filter by strategy
rco opportunities -g venda_de_put_semanal

# Filter by ticker
rco opportunities -t VALE3

# Sort by profit
rco opportunities --sort profit

# Sort by profit in ascending order
rco opportunities --sort profit -o asc
```

Options:
- `-s, --status`: Operation status (open, closed, exercised)
- `-g, --strategy`: Filter by strategy (repeatable)
- `-l, --limit`: Max rows to fetch (≤ 99)
- `--sort`: Sort by column (id, ticker, strategy, entry, current, profit, etc.)
- `-o, --order`: Sort order (asc, desc)
- `-t, --filter-ticker`: Filter by ticker
- `-f, --filter-strategy`: Filter by strategy
- `--raw`: Dump raw JSON instead of table

### Price

Show daily closing prices for a ticker.

```bash
# Show price history
rco price VALE3

# Show average of last 5 days
rco price VALE3 --avg 5

# Show only the average value
rco price VALE3 --avg 10 --quiet
```

Options:
- `-a, --avg`: Show arithmetic mean of last N days
- `--raw`: Print raw JSON instead of table
- `-q, --quiet`: Suppress table; print only average value

## Development

### Project Structure

```
rco/
├── cli.py              # Main CLI entry point
├── commands/
│   ├── opportunities.py # Opportunities command
│   ├── price.py        # Price command
│   └── shared.py       # Shared utilities
├── helpers.py          # Helper functions
└── utils/
    └── requests.py     # HTTP request utilities
```

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/rco-cli.git
cd rco-cli

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .
```

## License

MIT License
