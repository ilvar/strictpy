from pathlib import Path

from strictpy.model import Report
from strictpy.policy import scan_path
from strictpy.typecheck import run_basedpyright


def check_path(requested: Path) -> Report:
    diagnostics = run_basedpyright(requested)
    diagnostics.extend(scan_path(requested))
    return Report.from_diagnostics(diagnostics)
