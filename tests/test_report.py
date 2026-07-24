import json
import unittest
from typing import cast

from strictpy.model import Diagnostic, Location, Report


class ReportTests(unittest.TestCase):
    def test_sorts_diagnostics_and_counts_levels(self) -> None:
        location_b = Location("b.py", 2, 1, 2, 2, "b")
        location_a = Location("a.py", 1, 1, 1, 2, "a")
        report = Report.from_diagnostics(
            [
                Diagnostic("warning", "basedpyright", "b", "later", location_b),
                Diagnostic("error", "strictpy", "a", "first", location_a),
            ]
        )
        payload = cast(dict[str, object], json.loads(report.to_json()))
        diagnostics = cast(list[dict[str, object]], payload["diagnostics"])

        self.assertFalse(report.ok)
        self.assertEqual(report.error_count, 1)
        self.assertEqual(report.warning_count, 1)
        self.assertEqual(diagnostics[0]["code"], "a")
