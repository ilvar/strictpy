from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Literal

from strictpy.model import Report
from strictpy.project import create_project
from strictpy.runner import check_path
from strictpy.skills import install_detected


HELP = Path(__file__).with_name("help.txt").read_text(encoding="utf-8")
USAGE = (
    "usage: strictpy [--help] | strictpy [check] [path] | "
    "strictpy new <name> | strictpy install-skills"
)

type Command = Literal["help", "check", "new", "install-skills"]


@dataclass(frozen=True)
class Operation:
    command: Command
    argument: str | None = None


def main() -> int:
    operation = parse_arguments(sys.argv[1:])
    if operation is None:
        return 2

    if operation.command == "help":
        _ = sys.stdout.write(HELP)
        return 0

    try:
        if operation.command == "check":
            report = check_path(Path(operation.argument or "."))
        elif operation.command == "new":
            if operation.argument is None:
                _ = usage_error("new requires a project name")
                return 2
            _ = create_project(Path("."), operation.argument)
            report = clean_report()
        else:
            messages = install_detected()
            for message in messages:
                _ = sys.stderr.write(f"{message}\n")
            report = clean_report()
    except (OSError, RuntimeError, ValueError) as error:
        _ = sys.stderr.write(f"{error}\n")
        return 2

    _ = sys.stdout.write(report.to_json())
    return 0 if report.ok else 1


def parse_arguments(arguments: list[str]) -> Operation | None:
    if not arguments:
        return Operation("check", ".")

    first = arguments[0]
    if first in {"-h", "--help", "help"}:
        if len(arguments) == 1:
            return Operation("help")
        return usage_error("help does not accept additional arguments")

    if first == "check":
        return parse_optional_path(arguments)

    if first == "new":
        if len(arguments) == 2 and arguments[1] in {"-h", "--help"}:
            return Operation("help")
        if len(arguments) == 2:
            return Operation("new", arguments[1])
        if len(arguments) == 1:
            return usage_error("new requires a project name")
        return usage_error("new accepts exactly one project name")

    if first == "install-skills":
        if len(arguments) == 2 and arguments[1] in {"-h", "--help"}:
            return Operation("help")
        if len(arguments) == 1:
            return Operation("install-skills")
        return usage_error("install-skills does not accept arguments")

    if len(arguments) == 1:
        return Operation("check", first)
    return usage_error("too many arguments")


def parse_optional_path(arguments: list[str]) -> Operation | None:
    if len(arguments) == 1:
        return Operation("check", ".")
    if len(arguments) == 2:
        if arguments[1] in {"-h", "--help"}:
            return Operation("help")
        return Operation("check", arguments[1])
    return usage_error("check accepts at most one path")


def usage_error(message: str) -> None:
    _ = sys.stderr.write(f"{message}\n{USAGE}\n")
    return None


def clean_report() -> Report:
    return Report.from_diagnostics([])


if __name__ == "__main__":
    sys.exit(main())
