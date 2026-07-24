from pathlib import Path
import sys

from strictpy.runner import check_path


HELP = Path(__file__).with_name("help.txt").read_text(encoding="utf-8")
USAGE = "usage: strictpy [--help] | strictpy [check] [path]"


def main() -> int:
    arguments = sys.argv[1:]
    operation = parse_arguments(arguments)
    if operation is None:
        return 2
    if operation == "help":
        _ = sys.stdout.write(HELP)
        return 0

    try:
        report = check_path(Path(operation))
    except (OSError, RuntimeError, ValueError) as error:
        _ = sys.stderr.write(f"{error}\n")
        return 2

    _ = sys.stdout.write(report.to_json())
    return 0 if report.ok else 1


def parse_arguments(arguments: list[str]) -> str | None:
    if not arguments:
        return "."
    if arguments[0] in {"-h", "--help", "help"}:
        if len(arguments) == 1:
            return "help"
        return usage_error("help does not accept additional arguments")
    if arguments[0] == "check":
        if len(arguments) == 1:
            return "."
        if len(arguments) == 2:
            if arguments[1] in {"-h", "--help"}:
                return "help"
            return arguments[1]
        return usage_error("check accepts at most one path")
    if len(arguments) == 1:
        return arguments[0]
    return usage_error("too many arguments")


def usage_error(message: str) -> None:
    _ = sys.stderr.write(f"{message}\n{USAGE}\n")
    return None


if __name__ == "__main__":
    sys.exit(main())
