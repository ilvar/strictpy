import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import cast

from strictpy.skills import SKILL_CONTENT


ROOT = Path(__file__).resolve().parents[1]


class SkillTests(unittest.TestCase):
    def test_install_skills_detects_both_agents_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / ".codex").mkdir()
            (home / ".claude").mkdir()

            first = run_cli(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            assert_clean(first)

            codex = home / ".agents/skills/strictpy/SKILL.md"
            claude = home / ".claude/skills/strictpy/SKILL.md"
            self.assertEqual(codex.read_text(encoding="utf-8"), SKILL_CONTENT)
            self.assertEqual(claude.read_text(encoding="utf-8"), SKILL_CONTENT)

            second = run_cli(home)
            self.assertEqual(second.returncode, 0, second.stderr)
            assert_clean(second)
            self.assertIn("already current", second.stderr)

    def test_install_skills_refuses_modified_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / ".codex").mkdir()
            destination = home / ".agents/skills/strictpy/SKILL.md"
            destination.parent.mkdir(parents=True)
            _ = destination.write_text("custom skill\n", encoding="utf-8")

            completed = run_cli(home)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stdout, "")
            self.assertIn("refusing to overwrite", completed.stderr)
            self.assertEqual(
                destination.read_text(encoding="utf-8"), "custom skill\n"
            )

    def test_install_skills_requires_a_detected_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = run_cli(Path(temporary))
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stdout, "")
            self.assertIn("no supported agent installation detected", completed.stderr)


def run_cli(home: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    environment["USERPROFILE"] = str(home)
    environment["PATH"] = ""
    return subprocess.run(
        [sys.executable, "-m", "strictpy.cli", "install-skills"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_clean(completed: subprocess.CompletedProcess[str]) -> None:
    payload = cast(dict[str, object], json.loads(completed.stdout))
    if payload.get("ok") is not True:
        raise AssertionError(f"expected clean report: {payload}")
