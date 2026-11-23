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
