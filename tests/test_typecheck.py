from pathlib import Path
import tempfile
import unittest

from strictpy.typecheck import (
    basedpyright_command,
    basedpyright_config,
    discover_project_python,
)


class TypecheckTests(unittest.TestCase):
    def test_discovers_unix_project_virtual_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            _ = python.write_text("", encoding="utf-8")

            self.assertEqual(discover_project_python(root), python)

    def test_discovers_windows_project_virtual_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            python = root / ".venv" / "Scripts" / "python.exe"
            python.parent.mkdir(parents=True)
            _ = python.write_text("", encoding="utf-8")

            self.assertEqual(discover_project_python(root), python)

    def test_command_uses_project_python_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            _ = python.write_text("", encoding="utf-8")
            config = root / "strictpy-config.json"

            command = basedpyright_command(root, config)
            self.assertIn("--pythonpath", command)
            self.assertIn(str(python), command)

    def test_config_adds_project_and_src_import_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()

            config = basedpyright_config(root)
            self.assertEqual(
                config["extraPaths"],
                [str(root), str(root / "src")],
            )
