from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ParseResult:
    status: Literal["ok", "invalid"]
    value: int | None


def parse_count(text: str) -> ParseResult:
    if text.isdecimal():
        return ParseResult(status="ok", value=int(text))
    return ParseResult(status="invalid", value=None)
