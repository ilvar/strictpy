---
name: strictpy
description: Use strictpy when writing or modifying Python that must be fully typed, checked with BasedPyright, and free of exception-based control flow in project source.
---

# strictpy workflow

Use ordinary Python syntax, but treat `strictpy check` as the primary feedback oracle.

## Required loop

1. Inspect the existing project before editing.
2. Add explicit types to every parameter and return value.
3. Represent expected failure as data: tagged unions, dataclasses, enums, `None`, or explicit result values.
4. Do not use `Any`, `raise`, `try`, `except`, `except*`, `finally`, or `assert` in checked source.
5. Use `uv` for Python versions, dependency changes, locking, environment synchronization, and execution.
6. Run `strictpy check PATH` and parse the single JSON report from stdout.
7. Address every diagnostic and repeat until `ok` is true.
8. Run the locked project tests before submitting.

## Dependencies

For a project, change dependencies declaratively:

```bash
uv add PACKAGE
uv remove PACKAGE
uv sync --locked
uv run COMMAND
```

Commit `pyproject.toml` and `uv.lock` together. Do not use ad-hoc `pip install` commands to mutate a project environment.

For a standalone utility with third-party dependencies, use PEP 723 inline metadata:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3>=1.34",
#     "textual>=0.65",
# ]
# ///
```

Use `uv add --script SCRIPT PACKAGE` and `uv remove --script SCRIPT PACKAGE` to maintain the metadata. Use `uv lock --script SCRIPT` and commit `SCRIPT.lock` when reproducibility matters. A PEP 723 script is self-contained and must not depend on packages being present in the surrounding project environment.

## Generated projects

Create a pinned project with:

```bash
strictpy new project-name
cd project-name
uv sync --locked
uv run basedpyright --level warning --warnings .
uv run python -m unittest discover -s tests -v
strictpy check .
```

`tests/test_properties.py` contains a Hypothesis invariant. Replace it with domain invariants, keep generated strategies bounded, and add important minimized failures as explicit `@example` cases.

## Constraints

- Do not weaken or bypass BasedPyright settings.
- Do not suppress diagnostics with bare ignore comments.
- Do not parse stderr as diagnostics.
- Do not claim that library calls cannot raise; the policy forbids explicit exception control flow in checked project source.
