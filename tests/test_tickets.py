from datetime import date
from pathlib import Path

import pytest

from tickets import load_tickets


HEADER = "ticket_id,service_date,status\n"


def write_csv(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "tickets.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_row(tmp_path: Path) -> None:
    path = write_csv(tmp_path, HEADER + "001,2026-11-24,open\n")

    tickets, errors = load_tickets(path)

    assert not errors
    assert len(tickets) == 1
    assert tickets[0].ticket_id == "001"
    assert tickets[0].service_date == date(2026, 11, 24)
    assert tickets[0].status == "open"


def test_missing_field(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "service_date,status\n2026-11-24,open\n")

    tickets, errors = load_tickets(path)

    assert not tickets
    assert len(errors) == 1
    assert (errors[0].row_number, errors[0].field, errors[0].code) == (2, "ticket_id", "missing")


def test_bad_date(tmp_path: Path) -> None:
    path = write_csv(tmp_path, HEADER + "001,2026-02-30,open\n")

    tickets, errors = load_tickets(path)

    assert not tickets
    assert len(errors) == 1
    assert (errors[0].row_number, errors[0].field, errors[0].code) == (2, "service_date", "value_error")


def test_bad_enum(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    path = write_csv(tmp_path, HEADER + "private-id,2026-11-24,invalid\n002,2026-11-25,closed\n")

    with caplog.at_level("INFO", logger="tickets"):
        tickets, errors = load_tickets(path)

    assert [ticket.ticket_id for ticket in tickets] == ["002"]
    assert len(errors) == 1
    assert (errors[0].row_number, errors[0].field, errors[0].code) == (2, "status", "literal_error")
    assert "1 valid, 1 invalid" in caplog.text
    assert "private-id" not in caplog.text


def test_empty_file(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "")

    assert load_tickets(path) == ([], [])
