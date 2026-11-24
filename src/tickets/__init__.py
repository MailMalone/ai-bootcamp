import csv
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, ValidationError, field_validator


logger = logging.getLogger(__name__)


class Ticket(BaseModel):
    ticket_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    service_date: date = Field(strict=True)
    status: Literal["open", "in_progress", "closed"]

    @field_validator("service_date", mode="before")
    @classmethod
    def parse_service_date(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError("Use a valid date in YYYY-MM-DD format") from None

        if parsed.isoformat() != value:
            raise ValueError("Use a valid date in YYYY-MM-DD format")
        return parsed


@dataclass(frozen=True)
class RowError:
    row_number: int
    field: str
    code: str
    message: str


def load_tickets(path: Path) -> tuple[list[Ticket], list[RowError]]:
    """Return valid tickets and the first validation error for each invalid row."""
    tickets: list[Ticket] = []
    errors: list[RowError] = []

    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):
            try:
                tickets.append(Ticket.model_validate(row))
            except ValidationError as exc:
                error = exc.errors(include_input=False)[0]
                field = str(error["loc"][0])
                code = error["type"]
                errors.append(RowError(row_number, field, code, error["msg"]))
                logger.warning("Row %d: %s (%s)", row_number, field, code)

    logger.info("Loaded %d valid, %d invalid", len(tickets), len(errors))
    return tickets, errors
