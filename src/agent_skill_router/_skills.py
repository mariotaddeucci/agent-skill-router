"""Skill discovery and installation helpers."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from fastmcp.server.providers.skills._common import parse_frontmatter


@dataclass
class SkillEntry:
    """Metadata for a discovered skill."""

    name: str
    description: str
    directory: Path


def _skill_description(skill_dir: Path) -> str:
    """Extract the description from a skill directory's SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""
    try:
        content = skill_md.read_text(encoding="utf-8")
        frontmatter, _ = parse_frontmatter(content)
        return str(frontmatter.get("description", "")).strip()
    except OSError:
        return ""


def discover_skills(roots: list[Path]) -> list[SkillEntry]:
    """Scan a list of root directories and return all valid skills found.

    First-wins deduplication: if the same skill name appears in multiple roots,
    only the first occurrence is returned (mirrors SkillsDirectoryProvider behaviour).
    """
    seen: set[str] = set()
    skills: list[SkillEntry] = []
    for root in roots:
        if not root.exists():
            continue
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            if not (entry / "SKILL.md").exists():
                continue
            if entry.name in seen:
                continue
            seen.add(entry.name)
            skills.append(
                SkillEntry(
                    name=entry.name,
                    description=_skill_description(entry),
                    directory=entry,
                )
            )
    return skills


def install_skill(source: Path, dest_root: Path) -> Path:
    """Copy a skill directory into *dest_root*.

    *source* must be a directory containing a SKILL.md file.
    Returns the path to the installed skill directory.
    Raises ValueError if *source* is not a valid skill directory.
    Raises FileExistsError if a skill with the same name already exists at *dest_root*.
    """
    if not (source / "SKILL.md").exists():
        msg = f"{source} is not a valid skill directory (missing SKILL.md)"
        raise ValueError(msg)

    dest_root.mkdir(parents=True, exist_ok=True)
    dest = dest_root / source.name

    if dest.exists():
        raise FileExistsError(dest)

    shutil.copytree(source, dest)
    return dest
