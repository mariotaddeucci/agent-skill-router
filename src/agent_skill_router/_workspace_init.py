"""Workspace initialization logic for multi-agent friendly repositories."""

import shutil
from pathlib import Path

_INSTRUCTION_FILES = [
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    "GEMINI.md",
]

_SKILL_PROVIDER_DIRS = [
    ".agents/skills",
    ".cursor/skills",
    ".github/skills",
    ".gemini/skills",
    ".codex/skills",
    ".goose/skills",
    ".opencode/skills",
]

_CANONICAL_SKILLS_DIR = ".claude/skills"
_AGENTS_MD = "AGENTS.md"


def detect_instruction_files(workspace: Path) -> list[Path]:
    """Return paths of instruction files that exist and are real files (not symlinks), excluding AGENTS.md."""
    result: list[Path] = []
    for name in _INSTRUCTION_FILES:
        p = workspace / name
        if p.exists() and not p.is_symlink():
            result.append(p)
    return result


def merge_into_agents_md(
    workspace: Path,
    sources: list[Path],
    force: bool = False,
) -> list[str]:
    """Create AGENTS.md by merging content from source files.

    Returns list of action strings describing what was done (or would be done).
    If AGENTS.md already exists and force=False, it is left unchanged.
    """
    agents_md = workspace / _AGENTS_MD
    actions: list[str] = []

    if agents_md.exists() and not force:
        actions.append(f"SKIP {_AGENTS_MD} already exists (use --force to overwrite)")
        return actions

    if not sources:
        actions.append(f"SKIP no instruction files found to merge into {_AGENTS_MD}")
        return actions

    parts: list[str] = []
    for src in sources:
        rel = src.relative_to(workspace)
        content = src.read_text(encoding="utf-8").strip()
        if content:
            parts.append(f"<!-- merged from {rel} -->\n{content}")
            actions.append(f"MERGE {rel} → {_AGENTS_MD}")

    if parts:
        agents_md.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        action_verb = "OVERWRITE" if agents_md.exists() and force else "CREATE"
        actions.insert(0, f"{action_verb} {_AGENTS_MD}")

    return actions


def create_instruction_symlinks(
    workspace: Path,
    sources: list[Path],
    dry_run: bool = False,
) -> list[str]:
    """Replace source instruction files with symlinks pointing to AGENTS.md.

    Returns list of action strings describing what was done (or would be done).
    """
    agents_md = workspace / _AGENTS_MD
    actions: list[str] = []

    if not agents_md.exists() and not dry_run:
        actions.append(f"SKIP cannot create symlinks: {_AGENTS_MD} does not exist")
        return actions

    for src in sources:
        rel = src.relative_to(workspace)
        if dry_run:
            actions.append(f"SYMLINK {rel} → {_AGENTS_MD}")
            continue
        if src.exists() and not src.is_symlink():
            src.unlink()
        src.symlink_to(agents_md)
        actions.append(f"SYMLINK {rel} → {_AGENTS_MD}")

    also_create = [
        workspace / name
        for name in _INSTRUCTION_FILES
        if not (workspace / name).exists() and str(Path(name)) not in [str(s.relative_to(workspace)) for s in sources]
    ]
    for target in also_create:
        rel = target.relative_to(workspace)
        if dry_run:
            actions.append(f"SYMLINK {rel} → {_AGENTS_MD}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(agents_md)
        actions.append(f"SYMLINK {rel} → {_AGENTS_MD}")

    return actions


def detect_skill_dirs(workspace: Path) -> dict[str, Path]:
    """Return dict of {provider_dir: path} for skill dirs that exist and are not symlinks.

    Excludes the canonical .claude/skills/ directory.
    """
    result: dict[str, Path] = {}
    for rel in _SKILL_PROVIDER_DIRS:
        p = workspace / rel
        if p.exists() and not p.is_symlink():
            result[rel] = p
    return result


def consolidate_skills(
    workspace: Path,
    skill_dirs: dict[str, Path],
    force: bool = False,
    dry_run: bool = False,
) -> list[str]:
    """Move skills to .claude/skills/ and create symlinks in original locations.

    Returns list of action strings describing what was done (or would be done).
    """
    canonical = workspace / _CANONICAL_SKILLS_DIR
    actions: list[str] = []

    for rel, src_path in skill_dirs.items():
        dest = workspace / _CANONICAL_SKILLS_DIR

        if dry_run:
            actions.append(f"MOVE {rel} → {_CANONICAL_SKILLS_DIR}")
            actions.append(f"SYMLINK {rel} → {_CANONICAL_SKILLS_DIR}")
            continue

        if dest.exists() and not dest.is_symlink() and src_path != dest:
            if not force:
                actions.append(f"SKIP {rel}: {_CANONICAL_SKILLS_DIR} already exists (use --force to overwrite)")
                continue
            shutil.rmtree(dest)

        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src_path != dest:
                shutil.copytree(src_path, dest, dirs_exist_ok=True)
                shutil.rmtree(src_path)
                actions.append(f"MOVE {rel} → {_CANONICAL_SKILLS_DIR}")

        if not dry_run and not src_path.is_symlink():
            src_path.symlink_to(canonical)
        actions.append(f"SYMLINK {rel} → {_CANONICAL_SKILLS_DIR}")

    all_provider_dirs = [workspace / r for r in _SKILL_PROVIDER_DIRS]
    for p in all_provider_dirs:
        if p.exists() or p.is_symlink():
            continue
        rel = str(p.relative_to(workspace))
        if dry_run:
            actions.append(f"SYMLINK {rel} → {_CANONICAL_SKILLS_DIR}")
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.symlink_to(canonical)
        actions.append(f"SYMLINK {rel} → {_CANONICAL_SKILLS_DIR}")

    return actions


def init_workspace(
    workspace: Path,
    dry_run: bool = False,
    force: bool = False,
) -> list[str]:
    """Run all workspace initialization steps.

    Returns a combined list of action strings.
    """
    all_actions: list[str] = []

    sources = detect_instruction_files(workspace)

    if dry_run:
        if not (workspace / _AGENTS_MD).exists():
            if sources:
                all_actions.append(f"CREATE {_AGENTS_MD}")
                all_actions.extend(f"MERGE {src.relative_to(workspace)} → {_AGENTS_MD}" for src in sources)
            else:
                all_actions.append(f"SKIP no instruction files found to merge into {_AGENTS_MD}")
        for name in _INSTRUCTION_FILES:
            p = workspace / name
            if not p.is_symlink():
                all_actions.append(f"SYMLINK {name} → {_AGENTS_MD}")
    else:
        all_actions.extend(merge_into_agents_md(workspace, sources, force=force))
        all_actions.extend(create_instruction_symlinks(workspace, sources))

    skill_dirs = detect_skill_dirs(workspace)
    all_actions.extend(consolidate_skills(workspace, skill_dirs, force=force, dry_run=dry_run))

    return all_actions
