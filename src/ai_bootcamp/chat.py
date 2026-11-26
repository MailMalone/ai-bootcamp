import csv
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from random import uniform
from time import sleep

from anthropic import APIError, APIStatusError, Anthropic
from anthropic.types import MessageParam, Usage
from dotenv import load_dotenv


MODEL = "claude-haiku-4-5-20251001"
INPUT_USD_PER_MILLION = 1
OUTPUT_USD_PER_MILLION = 5
LOG_COLUMNS = ("timestamp", "model", "input_tokens", "output_tokens", "estimated_cost", "currency")


class IncompleteReply(Exception):
    """The stream ended before Claude finished the reply."""


def stream_reply(client: Anthropic, messages: list[MessageParam]) -> tuple[str, Usage]:
    for attempt in range(1, 4):
        chunks: list[str] = []
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=512,
                system="You are a helpful assistant. Keep replies concise.",
                messages=messages,
            ) as stream:
                for event in stream:
                    if event.type == "text" and event.text:
                        chunks.append(event.text)
                        print(event.text, end="", flush=True)
                    elif event.type == "message_stop":
                        break
                else:
                    raise IncompleteReply("The response stream ended early.")
                return "".join(chunks), stream.get_final_message().usage
        except APIStatusError as error:
            status = error.status_code
            transient = status == 429 or 500 <= status < 600
            if chunks or not transient or attempt == 3:
                raise
            sleep(2 ** (attempt - 1) + uniform(0, 0.5))
    raise AssertionError("Retry loop exited without a response or an error")


def log_usage(path: Path, usage: Usage) -> None:
    estimated_cost = (
        usage.input_tokens * INPUT_USD_PER_MILLION + usage.output_tokens * OUTPUT_USD_PER_MILLION
    ) / 1_000_000
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(LOG_COLUMNS)
        writer.writerow(
            (datetime.now(UTC).isoformat(), MODEL, usage.input_tokens, usage.output_tokens,
             f"{estimated_cost:.6f}", "USD")
        )


def chat_loop(client: Anthropic, cost_log: Path) -> None:
    history: list[MessageParam] = []
    while True:
        prompt = input("You: ").strip()
        if prompt.lower() == "quit":
            return
        if not prompt:
            continue
        if len(prompt) > 4_000:
            print("Please keep messages to 4,000 characters.", file=sys.stderr)
            continue

        user_message: MessageParam = {"role": "user", "content": prompt}
        print("Claude: ", end="", flush=True)
        try:
            answer, usage = stream_reply(client, [*history, user_message])
        except (APIError, IncompleteReply) as error:
            print()
            if isinstance(error, APIStatusError):
                print(f"Reply failed (HTTP {error.status_code}).", file=sys.stderr)
                if error.status_code in (401, 403):
                    return
            else:
                print("Reply failed before the stream finished.", file=sys.stderr)
            continue

        print()
        log_usage(cost_log, usage)
        if answer:
            history.extend((user_message, {"role": "assistant", "content": answer}))
            del history[:-10]


def main() -> int:
    load_dotenv(".env")
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Set ANTHROPIC_API_KEY in .env to start the chat.", file=sys.stderr)
        return 1

    try:
        with Anthropic(api_key=api_key, max_retries=0, timeout=30.0) as client:
            print("Type quit to exit.")
            chat_loop(client, Path("cost_log.csv"))
    except EOFError:
        print()
    except KeyboardInterrupt:
        print("\nChat cancelled.", file=sys.stderr)
        return 130
    except OSError as error:
        print(f"Could not write cost_log.csv: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
