from typing import Any


def parse_count(text) -> Any:
    assert text
    try:
        value: int = "not an integer"
        return int(text)
    except ValueError:
        raise RuntimeError("invalid count")
