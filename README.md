# strictpy

`strictpy` is a constrained Python profile and deterministic checking interface for coding agents. It keeps ordinary Python syntax, delegates semantic type analysis to BasedPyright, and adds source-policy checks that a type checker does not enforce.

## Current scope

The implemented workflow provides:

- one stable JSON report for all diagnostics;
- mandatory parameter and return annotations;
- strict, unavoidable BasedPyright analysis;
- no explicit `Any` in annotations;
- no `raise` statements;
- no `try`, `except`, `except*`, `else`, or `finally` exception machinery;
- no `assert` statements in checked source;
- deterministic file and diagnostic ordering;
- a complete embedded agent manual;
- Codex and Claude Code skill installation;
- deterministic project generation with Python 3.14.6, `uv.lock`, and Hypothesis.

The no-exceptions rule is syntactic. Python, strictpy itself, test frameworks, and third-party code can still raise internally. Strict Python project code should model expected failure as data, for example with tagged unions, result objects, `None`, enums, or explicit status values.

## Install

Using `uv`:

```bash
uv tool install git+https://github.com/ilvar/strictpy
```

Using `pipx`:

```bash
pipx install git+https://github.com/ilvar/strictpy
```

The package requires Python 3.14 or newer and exact-pins its BasedPyright runtime.

Install the bundled coding-agent skill after starting Codex or Claude Code at least once:

```bash
strictpy install-skills
```

It writes only to detected clients:

- Codex: `~/.agents/skills/strictpy/SKILL.md`
- Claude Code: `~/.claude/skills/strictpy/SKILL.md`

The operation is idempotent and refuses to overwrite modified skill content. Installing the Python package itself does not modify agent configuration.

## Usage

```bash
strictpy --help
strictpy check path/to/project
strictpy path/to/project
```

A missing path defaults to the current directory.

Operational commands write exactly one JSON document to stdout. Human-oriented operational failures and installation notices are written to stderr.

Exit statuses:

- `0`: clean report or successful project/skill installation;
- `1`: diagnostics remain;
- `2`: invalid invocation or operational failure.

## Create a project

```bash
strictpy new hello-strictpy
cd hello-strictpy
uv sync --locked
```

The generated project contains:

- `.python-version` pinned to Python 3.14.6;
- exact-pinned BasedPyright 1.39.9;
- exact-pinned Hypothesis 6.160.0;
- a committed `uv.lock`;
- a strict BasedPyright configuration;
- a bounded property-test scaffold.

Validate it with:

```bash
uv run basedpyright --level warning --warnings .
uv run python -m unittest discover -s tests -v
strictpy check .
```

## Property testing

`tests/test_properties.py` is the handoff between the coding agent and Hypothesis:

1. the agent states an observable invariant;
2. Hypothesis generates bounded inputs;
3. failures are shrunk to a minimal case;
4. important minimized cases can be committed as explicit `@example` decorators.

Hypothesis also stores a local example database under `.hypothesis/examples`. The generated `.gitignore` permits retaining that directory because Hypothesis is exact-pinned, but explicit `@example` cases remain the durable correctness mechanism.

## Stable policy codes

| Code | Rule |
| --- | --- |
| `strictpy::missing_parameter_type` | Every named parameter except `self` and `cls` requires an annotation. |
| `strictpy::missing_return_type` | Every function and async function requires a return annotation, including `-> None`. |
| `strictpy::no_any` | `typing.Any` and equivalent `Any` annotations are forbidden. |
| `strictpy::no_raise` | Explicit `raise` statements are forbidden. |
| `strictpy::no_try` | `try`, `except`, `except*`, `else`, and `finally` exception machinery is forbidden. |
| `strictpy::no_assert` | `assert` statements are forbidden. |
| `strictpy::syntax_error` | The file cannot be parsed as Python 3.14 syntax. |

BasedPyright diagnostics are exposed as `basedpyright::<rule>` where a rule is available.

## Development

```bash
python -m pip install -e .
basedpyright --level warning --warnings src tests
python -m unittest discover -s tests -v
strictpy check fixtures/clean
```

See [`AGENTS.md`](AGENTS.md) for repository-specific implementation rules.
