from pathlib import Path
import tempfile
import unittest

from strictpy.policy import scan_path


class PolicyTests(unittest.TestCase):
    def test_reports_annotations_any_and_exception_constructs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.py"
            _ = path.write_text(
                "from typing import Any\n"
                "\n"
                "def broken(value) -> Any:\n"
                "    assert value\n"
                "    try:\n"
                "        raise ValueError(value)\n"
                "    except ValueError:\n"
                "        return value\n",
                encoding="utf-8",
            )
            codes = [item.code for item in scan_path(path)]

        self.assertEqual(
            codes,
            [
                "strictpy::missing_parameter_type",
                "strictpy::no_any",
                "strictpy::no_assert",
                "strictpy::no_try",
                "strictpy::no_raise",
            ],
        )

    def test_accepts_typed_result_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "clean.py"
            _ = path.write_text(
                "def parse(value: str) -> int | None:\n"
                "    if value.isdecimal():\n"
                "        return int(value)\n"
                "    return None\n",
                encoding="utf-8",
            )
            diagnostics = scan_path(path)

        self.assertEqual(diagnostics, [])
