import json
from pathlib import Path
import subprocess
import sys
import unittest
from typing import cast


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_help_is_complete_plain_text(self) -> None:
        completed = run_cli("--help")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        for required in [
            "AGENT WORKFLOW",
            "STRICT RULES",
            "OUTPUT CONTRACT",
            "GENERATED PROJECTS",
            "UV DEPENDENCY WORKFLOW",
            "PROPERTY TESTING",
            "AGENT SKILLS",
            "LIMITS",
            "strictpy::no_raise",
            "hypothesis==6.160.0",
            "#!/usr/bin/env -S uv run --script",
            "uv add --script SCRIPT PACKAGE",
        ]:
            self.assertIn(required, completed.stdout)

    def test_help_aliases_are_identical(self) -> None:
        expected = run_cli("--help")
        for arguments in [
            ("-h",),
            ("help",),
            ("check", "--help"),
            ("new", "--help"),
            ("install-skills", "--help"),
        ]:
            actual = run_cli(*arguments)
            self.assertEqual(actual.returncode, 0, arguments)
            self.assertEqual(actual.stderr, "", arguments)
            self.assertEqual(actual.stdout, expected.stdout, arguments)

    def test_clean_fixture_passes(self) -> None:
        completed = run_cli("check", str(ROOT / "fixtures" / "clean"))
        payload = cast(dict[str, object], json.loads(completed.stdout))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["ok"], True)

    def test_broken_fixture_reports_policy_and_type_errors(self) -> None:
        completed = run_cli("check", str(ROOT / "fixtures" / "broken"))
        payload = cast(dict[str, object], json.loads(completed.stdout))
        raw_diagnostics = cast(list[dict[str, object]], payload["diagnostics"])
        codes = {cast(str, item["code"]) for item in raw_diagnostics}

        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("strictpy::missing_parameter_type", codes)
        self.assertIn("strictpy::no_try", codes)
        self.assertIn("strictpy::no_raise", codes)
        self.assertTrue(any(code.startswith("basedpyright::") for code in codes))


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "strictpy.cli", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
