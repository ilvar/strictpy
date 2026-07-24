from dataclasses import dataclass
import json
from typing import Literal


type Level = Literal["error", "warning"]
type Source = Literal["strictpy", "basedpyright"]


@dataclass(frozen=True)
class Location:
    file: str
    line: int
    column: int
    end_line: int
    end_column: int
    snippet: str

    def to_dict(self) -> dict[str, object]:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "snippet": self.snippet,
        }


@dataclass(frozen=True)
class Diagnostic:
    level: Level
    source: Source
    code: str
    message: str
    at: Location

    def sort_key(self) -> tuple[str, int, int, str, str]:
        return (
            self.at.file,
            self.at.line,
            self.at.column,
            self.code,
            self.message,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "source": self.source,
            "code": self.code,
            "message": self.message,
            "at": self.at.to_dict(),
        }


@dataclass(frozen=True)
class Report:
    ok: bool
    error_count: int
    warning_count: int
    diagnostics: tuple[Diagnostic, ...]

    @classmethod
    def from_diagnostics(cls, diagnostics: list[Diagnostic]) -> "Report":
        ordered = tuple(sorted(diagnostics, key=Diagnostic.sort_key))
        error_count = sum(item.level == "error" for item in ordered)
        warning_count = sum(item.level == "warning" for item in ordered)
        return cls(
            ok=error_count == 0,
            error_count=error_count,
            warning_count=warning_count,
            diagnostics=ordered,
        )

    def to_json(self) -> str:
        payload: dict[str, object] = {
            "ok": self.ok,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
