from dataclasses import dataclass
from pathlib import Path
import shutil


TEMPLATE_ROOT = Path(__file__).with_name("project_template")


@dataclass(frozen=True)
class TemplateFile:
    resource: str
    destination: str


TEMPLATE_FILES: tuple[TemplateFile, ...] = (
    TemplateFile("gitignore.txt", ".gitignore"),
    TemplateFile("python-version.txt", ".python-version"),
    TemplateFile("README.md", "README.md"),
    TemplateFile("pyproject.toml", "pyproject.toml"),
    TemplateFile("uv.lock", "uv.lock"),
    TemplateFile("package-init.py", "{{MODULE_NAME}}/__init__.py"),
    TemplateFile("main.py", "{{MODULE_NAME}}/main.py"),
    TemplateFile("test-properties.py", "tests/test_properties.py"),
)


def create_project(parent: Path, name: str) -> Path:
    module_name = validate_name(name)
    destination = parent / name
    staging = parent / f".{name}.strictpy-tmp"

    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    if staging.exists():
        raise ValueError(f"staging path already exists: {staging}")

    try:
        staging.mkdir()
        write_project(staging, name, module_name)
        _ = staging.rename(destination)
    except OSError as error:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError(f"failed to create project {destination}: {error}") from error

    return destination


def validate_name(name: str) -> str:
    if not name:
        raise ValueError("project name cannot be empty")
    if not name[0].isascii() or not name[0].islower():
        raise ValueError("project name must start with a lowercase ASCII letter")
    if any(
        not character.isascii()
        or not (character.islower() or character.isdigit() or character in {"-", "_"})
        for character in name
    ):
        raise ValueError(
            "project name may contain only lowercase ASCII letters, digits, '-' and '_'"
        )
    return name.replace("-", "_")


def write_project(project: Path, name: str, module_name: str) -> None:
    for item in TEMPLATE_FILES:
        destination_name = render(item.destination, name, module_name)
        destination = project / destination_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = TEMPLATE_ROOT / item.resource
        content = render(source.read_text(encoding="utf-8"), name, module_name)
        _ = destination.write_text(content, encoding="utf-8")


def render(content: str, name: str, module_name: str) -> str:
    return content.replace("{{PROJECT_NAME}}", name).replace(
        "{{MODULE_NAME}}", module_name
    )
