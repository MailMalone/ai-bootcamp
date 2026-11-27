from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Literal

from anthropic import APIError, APIStatusError, Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, ValidationError


ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "prompts"
SAMPLES = ROOT / "day5" / "samples.csv"
ACCURACY = ROOT / "day5" / "accuracy.csv"
MODEL = "claude-haiku-4-5-20251001"
TOOL_NAME = "submit_triage"


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment: Literal[
        "ventilator",
        "infusion pump",
        "patient monitor",
        "defibrillator",
        "oxygen concentrator",
        "suction pump",
        "dialysis machine",
        "anesthesia machine",
        "imaging system",
        "other",
    ]
    urgency: Literal["low", "medium", "high", "critical"]
    hospital: str | None
    next_action: str


def triage(client: Anthropic, complaint: str, version: str) -> TriageResult:
    prompt = (PROMPTS / f"{version}.md").read_text(encoding="utf-8")
    messages = [{"role": "user", "content": f"<complaint>\n{complaint}\n</complaint>"}]
    tool = {
        "name": TOOL_NAME,
        "description": "Return the equipment complaint classification.",
        "input_schema": TriageResult.model_json_schema(),
    }

    for attempt in range(2):
        response = client.messages.create(
            model=MODEL,
            max_tokens=256,
            temperature=0,
            system=prompt,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "tool", "name": TOOL_NAME},
        )
        tool_use = next(
            (block for block in response.content if block.type == "tool_use" and block.name == TOOL_NAME),
            None,
        )
        try:
            if tool_use is None:
                raise ValueError("Model did not return the triage tool result")
            return TriageResult.model_validate(tool_use.input)
        except (ValidationError, ValueError):
            if attempt == 1:
                raise ValueError("Model returned an invalid triage result twice") from None
            if tool_use is None:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": "Call the required triage tool with all four valid fields."})
            else:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": "The tool input failed local validation. Return a corrected result that matches the required schema and allowed values.",
                        "is_error": True,
                    }],
                })
    raise AssertionError("Validation retry loop ended unexpectedly")


def accuracy_fields() -> list[str]:
    return [
        "sample_id", "complaint", "expected_equipment", "expected_urgency",
        "expected_hospital", "expected_next_action",
        "v1_equipment", "v1_urgency", "v1_hospital", "v1_next_action", "v1_correct",
        "v2_equipment", "v2_urgency", "v2_hospital", "v2_next_action", "v2_correct",
        "row_type", "v1_accuracy_percent", "v2_accuracy_percent",
    ]


def write_accuracy(rows: list[dict[str, str]], summary: dict[str, str]) -> None:
    with ACCURACY.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=accuracy_fields())
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(summary)


def evaluate(client: Anthropic) -> None:
    fields = accuracy_fields()
    with SAMPLES.open(newline="", encoding="utf-8-sig") as file:
        samples = list(csv.DictReader(file))
    with ACCURACY.open(newline="", encoding="utf-8-sig") as file:
        existing = {row["sample_id"]: row for row in csv.DictReader(file) if row["row_type"] == "sample"}

    rows_by_id = {
        sample["sample_id"]: existing.get(sample["sample_id"], {key: "" for key in fields})
        for sample in samples
    }
    rows = list(rows_by_id.values())
    summary = {key: "" for key in fields}
    summary["sample_id"] = "OVERALL"
    summary["row_type"] = "overall"
    for sample in samples:
        row = rows_by_id[sample["sample_id"]]
        row.update(sample)
        row["row_type"] = "sample"

        for version in ("v1", "v2"):
            if row[f"{version}_correct"]:
                continue
            result = triage(client, sample["complaint"], version).model_dump()
            expected = {key: sample[f"expected_{key}"] for key in result}
            correct = all(
                ("" if value is None else str(value)).strip().casefold()
                == ("" if expected[key] is None else str(expected[key])).strip().casefold()
                for key, value in result.items()
            )
            for key, value in result.items():
                row[f"{version}_{key}"] = "" if value is None else str(value)
            row[f"{version}_correct"] = str(correct).lower()
            write_accuracy(rows, summary)

    for version in ("v1", "v2"):
        scores = [row[f"{version}_correct"] == "true" for row in rows]
        percentage = 100 * sum(scores) / len(scores) if scores else 0
        summary[f"{version}_accuracy_percent"] = f"{percentage:.1f}%"
    write_accuracy(rows, summary)


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage equipment complaints with Claude.")
    parser.add_argument("complaint", nargs="?", help="equipment complaint to classify")
    parser.add_argument("--evaluate", action="store_true", help="score both prompts on the 20 sample complaints")
    args = parser.parse_args()
    if args.evaluate == bool(args.complaint):
        parser.error("provide a complaint or use --evaluate")

    load_dotenv(ROOT / ".env")
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Set ANTHROPIC_API_KEY in .env to use the triager.", file=sys.stderr)
        return 1

    try:
        with Anthropic(api_key=api_key, max_retries=0, timeout=30.0) as client:
            if args.evaluate:
                evaluate(client)
                print(f"Scored 20 complaints with both prompts. See {ACCURACY.relative_to(ROOT)}.")
            else:
                result = triage(client, args.complaint, "v2")
                print(result.model_dump_json(indent=2))
    except APIError as error:
        if isinstance(error, APIStatusError):
            print(f"Claude API request failed with HTTP {error.status_code}.", file=sys.stderr)
        else:
            print("Claude API request failed.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Triage could not be completed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
