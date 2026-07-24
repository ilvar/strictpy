# AGENTS.md

## Project intent

`strictpy` is ordinary Python plus a strict source profile and deterministic feedback contract for coding agents. Do not create a new parser, runtime, Python fork, or syntax extension.

## Diagnostic contract

Operational commands must emit exactly one JSON document to stdout. Keep human operational failures on stderr.

Required properties:

- deterministic ordering by `(file, line, column, code, message)`;
- one-based line and column positions;
- `source` is `strictpy` or `basedpyright`;
- stable `strictpy::` policy codes;
- exit `0` only for a clean report, `1` for diagnostics, and `2` for invocation or operational failure;
- never hide or downgrade project configuration errors;
- never trust a target project's BasedPyright configuration to weaken checks.

## Strict subset

Checked source must:

- annotate every parameter except conventional `self` and `cls`;
- annotate every function return, including `-> None`;
- avoid explicit `Any` annotations;
- avoid `raise`;
- avoid all `try` forms and therefore `except`, `except*`, `else`, and `finally` handlers;
- avoid `assert`;
- pass BasedPyright in `all` mode with warnings treated as failures.

Expected failure should be represented as data with unions, dataclasses, enums, `None`, or explicit result values.

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
basedpyright --level warning src tests
python -m unittest discover -s tests -v
strictpy check fixtures/clean
```

The broken fixture must continue to prove simultaneous policy and type diagnostics. Batch related changes and avoid using CI as a substitute for local validation.
