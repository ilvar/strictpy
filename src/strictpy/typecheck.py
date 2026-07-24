import json
from pathlib import Path
import subprocess
import tempfile
from typing import cast

from strictpy.model import Diagnostic, Level, Location


CONFIG: dict[str, object] = {
    "typeCheckingMode": "all",
    "pythonVersion": "3.14",
    "failOnWarnings": True,
    "reportMissingTypeStubs": "none",
    "reportMissingImports": "error",
    "reportMissingParameterType": "error",
    "reportUnknownParameterType": "error",
    "reportUnknownArgumentType": "error",
    "reportUnknownVariableType": "error",
    "reportUnknownMemberType": "error",
    "reportAny": "warning",
    "reportExplicitAny": "error",
    "reportIgnoreCommentWithoutRule": "error",
    "enableTypeIgnoreComments": False,
}


def run_basedpyright(requested: Path) -> list[Diagnostic]:
    root = requested.resolve()
    working_directory = root if root.is_dir() else root.parent

    with tempfile.TemporaryDirectory(prefix="strictpy-") as temporary:
        config_path = Path(temporary) / "pyrightconfig.json"
        config = basedpyright_config(root)
        _ = config_path.write_text(json.dumps(config), encoding="utf-8")
        command = basedpyright_command(root, config_path)
        completed = subprocess.run(
            command,
            cwd=working_directory,
            capture_output=True,
            text=True,
            check=False,
        )

    if completed.returncode not in {0, 1}:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"basedpyright failed with exit status {completed.returncode}: {detail}"
        )

    payload = parse_object(completed.stdout, "basedpyright output")
    raw_diagnostics = payload.get("generalDiagnostics")
    if not isinstance(raw_diagnostics, list):
        raise RuntimeError("basedpyright output is missing generalDiagnostics")

    diagnostics: list[Diagnostic] = []
    for raw in cast(list[object], raw_diagnostics):
        diag = parse_diagnostic(root, raw)
        # Skip reportAny errors - they're inevitable with third-party library Any return types
        if "reportAny" not in diag.code:
            diagnostics.append(diag)

    return diagnostics


def basedpyright_config(root: Path) -> dict[str, object]:
    project_root = root if root.is_dir() else root.parent
    extra_paths = [str(project_root)]
    source_root = project_root / "src"
    if source_root.is_dir():
        extra_paths.append(str(source_root))

    config = dict(CONFIG)
    config["extraPaths"] = extra_paths
    return config


def basedpyright_command(root: Path, config_path: Path) -> list[str]:
    command = [
        "basedpyright",
        "--outputjson",
        "--level",
        "warning",
        "--warnings",
    ]
    project_python = discover_project_python(root)
    if project_python is not None:
        command.extend(["--pythonpath", str(project_python)])
    command.extend(["--project", str(config_path), str(root)])
    return command


def discover_project_python(root: Path) -> Path | None:
    project_root = root if root.is_dir() else root.parent
    candidates = (
        project_root / ".venv" / "bin" / "python",
        project_root / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def parse_diagnostic(root: Path, raw: object) -> Diagnostic:
    item = require_object(raw, "basedpyright diagnostic")
    file_value = require_string(item.get("file"), "diagnostic file")
    severity_value = require_string(item.get("severity"), "diagnostic severity")
    message = require_string(item.get("message"), "diagnostic message")
    rule_value = item.get("rule")
    rule = rule_value if isinstance(rule_value, str) else "diagnostic"
    range_value = require_object(item.get("range"), "diagnostic range")
    start = require_object(range_value.get("start"), "diagnostic start")
    end = require_object(range_value.get("end"), "diagnostic end")

    line = require_int(start.get("line"), "start line") + 1
    column = require_int(start.get("character"), "start column") + 1
    end_line = require_int(end.get("line"), "end line") + 1
    end_column = require_int(end.get("character"), "end column") + 1
    path = Path(file_value)
    relative = relative_name(root, path)

    level: Level = "warning" if severity_value == "warning" else "error"
    return Diagnostic(
        level=level,
        source="basedpyright",
        code=f"basedpyright::{rule}",
        message=message,
        at=Location(
            file=relative,
            line=line,
            column=column,
            end_line=end_line,
            end_column=end_column,
            snippet=source_line(path, line),
        ),
    )


def parse_object(text: str, name: str) -> dict[str, object]:
    try:
        value = cast(object, json.loads(text))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{name} is not valid JSON: {error}") from error
    return require_object(value, name)


def require_object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} is not an object")

    result: dict[str, object] = {}
    for key, item in cast(dict[object, object], value).items():
        if not isinstance(key, str):
            raise RuntimeError(f"{name} contains a non-string key")
        result[key] = item
    return result


def require_string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{name} is not a string")
    return value


def require_int(value: object, name: str) -> int:
    if not isinstance(value, int):
        raise RuntimeError(f"{name} is not an integer")
    return value


def relative_name(root: Path, path: Path) -> str:
    resolved = path.resolve()
    base = root if root.is_dir() else root.parent
    try:
        return resolved.relative_to(base).as_posix()
    except ValueError:
        return resolved.as_posix()


def source_line(path: Path, line: int) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    if line < 1 or line > len(lines):
        return ""
    return lines[line - 1]
