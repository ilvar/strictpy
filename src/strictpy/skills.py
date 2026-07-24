from dataclasses import dataclass
import os
from pathlib import Path
import shutil


SKILL_CONTENT = (
    Path(__file__)
    .with_name("skills")
    .joinpath("strictpy", "SKILL.md")
    .read_text(encoding="utf-8")
)


@dataclass(frozen=True)
class SkillTarget:
    agent: str
    path: Path


def install_detected() -> list[str]:
    home = home_directory()
    targets = detected_targets(home)
    if not targets:
        raise RuntimeError(
            "no supported agent installation detected; start Codex or Claude Code once, "
            "then rerun `strictpy install-skills`"
        )

    preflight(targets)
    created: list[Path] = []
    messages: list[str] = []

    try:
        for target in targets:
            if target.path.is_file():
                messages.append(
                    f"{target.agent} skill is already current: {target.path}"
                )
                continue

            target.path.parent.mkdir(parents=True, exist_ok=True)
            with target.path.open("x", encoding="utf-8") as handle:
                _ = handle.write(SKILL_CONTENT)
            created.append(target.path)
            messages.append(f"installed {target.agent} skill: {target.path}")
    except OSError as error:
        for path in created:
            path.unlink(missing_ok=True)
        raise RuntimeError(f"failed to install agent skill: {error}") from error

    return messages


def home_directory() -> Path:
    value = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if value is None:
        raise RuntimeError("cannot determine the user home directory")
    return Path(value)


def detected_targets(home: Path) -> list[SkillTarget]:
    targets: list[SkillTarget] = []
    if (
        (home / ".codex").is_dir()
        or (home / ".agents").is_dir()
        or shutil.which("codex") is not None
    ):
        targets.append(
            SkillTarget(
                agent="Codex",
                path=home / ".agents" / "skills" / "strictpy" / "SKILL.md",
            )
        )
    if (home / ".claude").is_dir() or shutil.which("claude") is not None:
        targets.append(
            SkillTarget(
                agent="Claude Code",
                path=home / ".claude" / "skills" / "strictpy" / "SKILL.md",
            )
        )
    return targets


def preflight(targets: list[SkillTarget]) -> None:
    for target in targets:
        if not target.path.exists():
            continue
        if not target.path.is_file():
            raise RuntimeError(
                f"skill destination is not a file for {target.agent}: {target.path}"
            )
        existing = target.path.read_text(encoding="utf-8")
        if existing != SKILL_CONTENT:
            raise RuntimeError(
                f"refusing to overwrite a modified {target.agent} skill at "
                f"{target.path}; remove it explicitly and rerun the command"
            )
