# AGENTS.md

## Project intent

`strictpy` is ordinary Python plus a strict source profile and deterministic feedback contract for coding agents. Do not create a new parser, runtime, Python fork, or syntax extension.

## Diagnostic contract

Operational commands must emit exactly one JSON document to stdout. Help is the only plain-text stdout mode. Keep human operational failures and installation notices on stderr.

Required properties:

- deterministic ordering by `(file, line, column, code, message)`;
- one-based line and column positions;
- `source` is `strictpy` or `basedpyright`;
- stable `strictpy::` policy codes;
- exit `0` only for a clean report or successful non-check operation, `1` for diagnostics, and `2` for invocation or operational failure;
- never hide or downgrade project configuration errors;
- never trust a target project's BasedPyright configuration to weaken checks.

## Strict subset

Checked project source must:

- annotate every parameter except conventional `self` and `cls`;
- annotate every function return, including `-> None`;
- avoid explicit `Any` annotations;
- avoid `raise`;
- avoid all `try` forms and therefore `except`, `except*`, `else`, and `finally` handlers;
- avoid `assert`;
- pass BasedPyright in `all` mode with warnings treated as failures.

Expected failure should be represented as data with unions, dataclasses, enums, `None`, or explicit result values. The rule is syntactic and does not imply that Python or dependencies cannot raise internally.

## uv dependency workflow

Use `uv` for Python versions, dependency changes, locking, environment synchronization, and execution.

For projects:

- use `uv add PACKAGE` and `uv remove PACKAGE` instead of ad-hoc `pip install` or direct environment mutation;
- commit `pyproject.toml` and `uv.lock` together;
- use `uv sync --locked` for reproducible setup;
- execute tools and modules through `uv run`.

For standalone scripts with third-party dependencies, use PEP 723 inline metadata and the executable shebang:

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

Manage script dependencies with `uv add --script SCRIPT PACKAGE` and `uv remove --script SCRIPT PACKAGE`. Use `uv lock --script SCRIPT` and commit the adjacent `.lock` file when reproducibility matters. Inline-script dependencies are self-contained and must not rely on the surrounding project's environment.

## Agent-help contract

`src/strictpy/help.txt` is a public operational manual. It must document every command, strict rule, report field, exit status, generated-project workflow, uv dependency workflow, property-test workflow, agent-skill destination, and the limits of the no-exceptions claim.

All help aliases must print identical text to stdout and exit successfully:

- `--help`
- `-h`
- `help`
- `check --help`
- `new --help`
- `install-skills --help`

## Agent-skill rules

The bundled portable skill lives at `src/strictpy/skills/strictpy/SKILL.md`.

`strictpy install-skills` must:

- detect Codex from `~/.codex`, `~/.agents`, or a `codex` executable;
- install Codex content to `~/.agents/skills/strictpy/SKILL.md`;
- detect Claude Code from `~/.claude` or a `claude` executable;
- install Claude content to `~/.claude/skills/strictpy/SKILL.md`;
- preflight every destination before writing;
- be idempotent when content matches;
- refuse to overwrite modified content;
- leave package installation itself side-effect free.

## Project-template rules

`strictpy new <name>` must create a deterministic project through a staging directory and final rename. It must reject invalid names, existing destinations, and existing staging paths.

Generated projects must contain:

- Python 3.14.6 in `.python-version`;
- exact-pinned BasedPyright and Hypothesis versions;
- a committed `uv.lock`;
- a strict BasedPyright editor configuration;
- no runtime dependencies;
- a bounded Hypothesis property test;
- validation instructions for `uv sync --locked`, BasedPyright, unittest, and strictpy;
- instructions to use `uv add` for project dependencies and PEP 723 metadata for standalone scripts.

When a pinned version changes, update the template manifest, lockfile, help, README, tests, and CI in one coherent change.

## Property-testing rules

- State observable invariants rather than duplicating implementations.
- Keep strategies bounded for fast deterministic CI.
- Treat the Hypothesis database as a cache, not the correctness contract.
- Add important minimized failures as explicit `@example` cases.
- Keep Hypothesis exact-pinned if `.hypothesis/examples` is shared or committed.

## Implementation rules

- Prefer standard-library Python around the exact-pinned BasedPyright executable.
- Use Python's `ast` module for source-policy checks.
- Do not infer types independently of BasedPyright.
- Generate a private temporary BasedPyright configuration so target repositories cannot weaken checking.
- Normalize paths relative to the requested project root.
- Exclude only conventional generated or environment directories.
- Preserve source snippets and exact ranges where available.
- Treat malformed BasedPyright JSON or unsupported exit statuses as operational failures.

## Validation

Before pushing:

```bash
uv run basedpyright --level warning --warnings src tests
uv run python -m unittest discover -s tests -v
uv run strictpy check fixtures/clean
```

For generated-project changes, additionally install `uv==0.11.29`, generate a project, and run:

```bash
uv sync --locked
uv run basedpyright --level warning --warnings .
uv run python -m unittest discover -s tests -v
strictpy check .
```

The broken fixture must continue to prove simultaneous policy and type diagnostics. Batch related changes and avoid using CI as a substitute for validation available locally.
