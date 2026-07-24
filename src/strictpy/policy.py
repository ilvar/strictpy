import ast
from pathlib import Path
from typing import override

from strictpy.model import Diagnostic, Location


EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)


def scan_path(requested: Path) -> list[Diagnostic]:
    root = requested.resolve()
    files = discover_files(root)
    diagnostics: list[Diagnostic] = []

    for path in files:
        diagnostics.extend(scan_file(root, path))

    return diagnostics


def discover_files(root: Path) -> list[Path]:
    if root.is_file():
        if root.suffix not in {".py", ".pyi"}:
            raise ValueError(f"not a Python source file: {root}")
        return [root]

    if not root.is_dir():
        raise ValueError(f"path does not exist: {root}")

    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".pyi"}
        and not any(part in EXCLUDED_DIRECTORIES for part in path.relative_to(root).parts)
    ]
    return sorted(files)


def scan_file(root: Path, path: Path) -> list[Diagnostic]:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    relative = relative_name(root, path)

    try:
        tree = ast.parse(source, filename=relative, type_comments=True)
    except SyntaxError as error:
        line = error.lineno or 1
        column = error.offset or 1
        end_line = error.end_lineno or line
        end_column = error.end_offset or column
        snippet = line_text(lines, line)
        return [
            Diagnostic(
                level="error",
                source="strictpy",
                code="strictpy::syntax_error",
                message=error.msg,
                at=Location(
                    file=relative,
                    line=line,
                    column=column,
                    end_line=end_line,
                    end_column=end_column,
                    snippet=snippet,
                ),
            )
        ]

    visitor = PolicyVisitor(relative, lines)
    visitor.visit(tree)
    return visitor.diagnostics


def relative_name(root: Path, path: Path) -> str:
    if root.is_file():
        return path.name
    return path.relative_to(root).as_posix()


def line_text(lines: list[str], line: int) -> str:
    if line < 1 or line > len(lines):
        return ""
    return lines[line - 1]


class PolicyVisitor(ast.NodeVisitor):
    def __init__(self, file: str, lines: list[str]) -> None:
        self.file = file
        self.lines = lines
        self.diagnostics: list[Diagnostic] = []

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    @override
    def visit_Raise(self, node: ast.Raise) -> None:
        # Allow raise if marked with # strictpy: allow-raise
        if not self._is_exempted(node, "strictpy: allow-raise"):
            self._add(
                node,
                "strictpy::no_raise",
                "exceptions are forbidden; represent failure as data",
            )
        self.generic_visit(node)

    @override
    def visit_Try(self, node: ast.Try) -> None:
        # Allow try/except if marked with # strictpy: allow-try
        if not self._is_exempted(node, "strictpy: allow-try"):
            self._add(
                node,
                "strictpy::no_try",
                "exception handling is forbidden; use explicit result values",
            )
        self.generic_visit(node)

    @override
    def visit_TryStar(self, node: ast.TryStar) -> None:
        self._add(
            node,
            "strictpy::no_try",
            "exception-group handling is forbidden; use explicit result values",
        )
        self.generic_visit(node)

    @override
    def visit_Assert(self, node: ast.Assert) -> None:
        self._add(
            node,
            "strictpy::no_assert",
            "assert is forbidden because it raises AssertionError",
        )
        self.generic_visit(node)

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check_any(node.annotation)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        for argument in arguments:
            if argument.arg in {"self", "cls"}:
                continue
            if argument.annotation is None:
                self._add(
                    argument,
                    "strictpy::missing_parameter_type",
                    f"parameter '{argument.arg}' requires a type annotation",
                )
            else:
                self._check_any(argument.annotation)

        for argument in [node.args.vararg, node.args.kwarg]:
            if argument is None:
                continue
            if argument.annotation is None:
                self._add(
                    argument,
                    "strictpy::missing_parameter_type",
                    f"parameter '{argument.arg}' requires a type annotation",
                )
            else:
                self._check_any(argument.annotation)

        if node.returns is None:
            self._add(
                node,
                "strictpy::missing_return_type",
                f"function '{node.name}' requires an explicit return annotation",
            )
        else:
            self._check_any(node.returns)

    def _check_any(self, annotation: ast.expr) -> None:
        for child in ast.walk(annotation):
            if isinstance(child, ast.Name) and child.id == "Any":
                self._add(
                    child,
                    "strictpy::no_any",
                    "Any is forbidden; use a precise type or a checked union",
                )
            elif isinstance(child, ast.Attribute) and child.attr == "Any":
                self._add(
                    child,
                    "strictpy::no_any",
                    "Any is forbidden; use a precise type or a checked union",
                )

    def _is_exempted(self, node: ast.AST, exemption: str) -> bool:
        """Check if a node is exempted via a comment like # strictpy: allow-try"""
        line = getattr(node, "lineno", 1)
        line_str = line_text(self.lines, line)
        return exemption in line_str

    def _add(self, node: ast.AST, code: str, message: str) -> None:
        line = getattr(node, "lineno", 1)
        column = getattr(node, "col_offset", 0) + 1
        end_line = getattr(node, "end_lineno", line)
        end_column = getattr(node, "end_col_offset", column - 1) + 1
        self.diagnostics.append(
            Diagnostic(
                level="error",
                source="strictpy",
                code=code,
                message=message,
                at=Location(
                    file=self.file,
                    line=line,
                    column=column,
                    end_line=end_line,
                    end_column=end_column,
                    snippet=line_text(self.lines, line),
                ),
            )
        )
