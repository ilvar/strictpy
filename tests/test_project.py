import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import cast


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = [
    ".gitignore",
    ".python-version",
    "README.md",
    "hello_strictpy/__init__.py",
    "hello_strictpy/main.py",
    "pyproject.toml",
    "tests/test_properties.py",
    "uv.lock",
]


class ProjectTests(unittest.TestCase):
    def test_new_creates_pinned_property_test_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            completed = run_cli(root, "new", "hello-strictpy")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = cast(dict[str, object], json.loads(completed.stdout))
            self.assertEqual(payload["ok"], True)

            generated = root / "hello-strictpy"
            self.assertEqual(relative_files(generated), EXPECTED_FILES)
            self.assertEqual(
                (generated / ".python-version").read_text(encoding="utf-8"),
                "3.14.6\n",
            )

            manifest = (generated / "pyproject.toml").read_text(encoding="utf-8")
            self.assertIn('name = "hello-strictpy"', manifest)
            self.assertIn('"basedpyright==1.39.9"', manifest)
            self.assertIn('"hypothesis==6.160.0"', manifest)
            self.assertIn('include = ["hello_strictpy", "tests"]', manifest)

            properties = (generated / "tests/test_properties.py").read_text(
                encoding="utf-8"
            )
            self.assertIn("from hypothesis import given, strategies as st", properties)
            self.assertIn("max_size=64", properties)
            self.assertIn("hello_strictpy.main", properties)

            readme = (generated / "README.md").read_text(encoding="utf-8")
            self.assertIn("uv add PACKAGE", readme)
            self.assertIn("#!/usr/bin/env -S uv run --script", readme)
            self.assertIn("uv lock --script SCRIPT", readme)

    def test_new_refuses_invalid_and_existing_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid = run_cli(root, "new", "../escape")
            self.assertEqual(invalid.returncode, 2)
            self.assertFalse((root.parent / "escape").exists())

            (root / "already-there").mkdir()
            existing = run_cli(root, "new", "already-there")
            self.assertEqual(existing.returncode, 2)
            self.assertIn("destination already exists", existing.stderr)


def run_cli(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "strictpy.cli", *arguments],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )


def relative_files(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )
