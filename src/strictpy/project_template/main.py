import sys


def reverse(values: list[int]) -> list[int]:
    return list(reversed(values))


def main() -> int:
    _ = sys.stdout.write("Hello from {{PROJECT_NAME}}.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
