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

## Day 3 — Analyze vendor payments in PostgreSQL

Start a fresh PostgreSQL 16 container and run the scripts from the repository root:

```sh
docker run -d --name bootcamp-day3 --network none -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=bootcamp_day3 postgres:16-alpine
docker cp day3 bootcamp-day3:/tmp/day3
docker exec bootcamp-day3 pg_isready -U postgres -d bootcamp_day3
docker exec -w /tmp/day3 bootcamp-day3 psql -X -U postgres -d bootcamp_day3 -v ON_ERROR_STOP=1 -f load.sql -f queries.sql -f index.sql
```

Run the last command once PostgreSQL reports that it is accepting connections. The load should report 123 rows. See the [five findings](day3/insights.md) and the [index comparison](day3/insights.md#index-comparison).

The CSV comes from the [reference bootcamp's Day 3 branch](https://github.com/PranavBShenoy/ai-studio-bootcamp/blob/3631f2b7ee07606d72029e57ae8416f05d16f336/vendor_payments.csv).
