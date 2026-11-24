# AI Bootcamp

This repository holds my AI Studio Bootcamp exercises. The Day 1 starter is a Python command-line app that prints a greeting so you can verify your development setup.

## Setup and run

Install Python 3.12 and [uv](https://docs.astral.sh/uv/). From the repository root, run:

```sh
uv sync
uv run ai-bootcamp
```

Expected output:

```text
Hello from ai-bootcamp!
```

The starter runs without API keys. When an exercise needs credentials, copy `.env.example` to `.env` and fill in the values locally. Keep `.env` out of Git.

## Day 2 — Validate service tickets

Use a UTF-8 CSV with these required columns. The service date uses `YYYY-MM-DD`. Status is `open`, `in_progress`, or `closed`.

```csv
ticket_id,service_date,status
001,2026-11-24,open
```

Save the example as `tickets.csv`, run `uv run python`, then enter:

```python
from pathlib import Path
from tickets import load_tickets

tickets, errors = load_tickets(Path("tickets.csv"))
```

The loader returns two lists. Each invalid row is reported by its record number, field, and first validation error. The header counts as record 1. An empty or header-only file returns two empty lists.

Run the tests with `uv run pytest -v`.
