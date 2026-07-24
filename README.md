# strictpy

`strictpy` is a constrained Python profile and deterministic checking interface for coding agents. It keeps ordinary Python syntax, delegates semantic type analysis to BasedPyright, and adds source-policy checks that a type checker does not enforce.

## Current scope

The initial release provides:

- one stable JSON report for all diagnostics;
- mandatory parameter and return annotations;
- strict, unavoidable BasedPyright analysis;
- no explicit `Any` in annotations;
- no `raise` statements;
- no `try`, `except`, `except*`, `else`, or `finally` exception machinery;
- no `assert` statements, because they raise `AssertionError` at runtime;
- deterministic file and diagnostic ordering.

The no-exceptions rule is syntactic. Python and third-party code can still fail at runtime. Strict Python code should model expected failure as data, for example with tagged unions, result objects, `None`, or explicit status values.

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

## Usage

```bash
strictpy --help
strictpy check path/to/project
strictpy path/to/project
```

A missing path defaults to the current directory.

Operational commands write exactly one JSON document to stdout. Human-oriented operational failures are written to stderr.

Exit statuses:

- `0`: the project is clean;
- `1`: diagnostics remain;
- `2`: invalid invocation or operational failure.

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

## Example

Allowed:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ParseResult:
    status: Literal["ok", "invalid"]
    value: int | None


def parse_count(text: str) -> ParseResult:
    if text.isdecimal():
        return ParseResult(status="ok", value=int(text))
    return ParseResult(status="invalid", value=None)
```

Rejected:

```python
def parse_count(text):
    try:
        return int(text)
    except ValueError:
        raise RuntimeError("invalid count")
```

## Development

```bash
python -m pip install -e .
basedpyright --level warning src tests
python -m unittest discover -s tests -v
strictpy check fixtures/clean
```

See [`AGENTS.md`](AGENTS.md) for repository-specific implementation rules.
