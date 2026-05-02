"""Tests for _workspace_init.py — multi-agent friendly workspace initialization."""

from agent_skill_router._workspace_init import (
    _AGENTS_MD,
    _CANONICAL_SKILLS_DIR,
    consolidate_skills,
    create_instruction_symlinks,
    detect_instruction_files,
    detect_skill_dirs,
    init_workspace,
    merge_into_agents_md,
)


def test_detect_instruction_files_empty(tmp_path):
    assert detect_instruction_files(tmp_path) == []


def test_detect_instruction_files_real_file(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Claude", encoding="utf-8")
    result = detect_instruction_files(tmp_path)
    assert len(result) == 1
    assert result[0].name == "CLAUDE.md"


def test_detect_instruction_files_skips_symlinks(tmp_path):
    agents_md = tmp_path / _AGENTS_MD
    agents_md.write_text("# Agents", encoding="utf-8")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.symlink_to(agents_md)
    assert detect_instruction_files(tmp_path) == []


def test_detect_instruction_files_multiple(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Claude", encoding="utf-8")
    gh = tmp_path / ".github"
    gh.mkdir()
    (gh / "copilot-instructions.md").write_text("# Copilot", encoding="utf-8")
    result = detect_instruction_files(tmp_path)
    names = [p.name for p in result]
    assert "CLAUDE.md" in names
    assert "copilot-instructions.md" in names


def test_merge_creates_agents_md(tmp_path):
    src = tmp_path / "CLAUDE.md"
    src.write_text("# Claude content", encoding="utf-8")
    actions = merge_into_agents_md(tmp_path, [src])
    agents_md = tmp_path / _AGENTS_MD
    assert agents_md.exists()
    assert "Claude content" in agents_md.read_text(encoding="utf-8")
    assert any("CREATE" in a or "MERGE" in a for a in actions)


def test_merge_skips_if_agents_md_exists_without_force(tmp_path):
    (tmp_path / _AGENTS_MD).write_text("# existing", encoding="utf-8")
    src = tmp_path / "CLAUDE.md"
    src.write_text("# new", encoding="utf-8")
    actions = merge_into_agents_md(tmp_path, [src])
    assert any("SKIP" in a for a in actions)
    assert (tmp_path / _AGENTS_MD).read_text(encoding="utf-8") == "# existing"


def test_merge_overwrites_with_force(tmp_path):
    (tmp_path / _AGENTS_MD).write_text("# old", encoding="utf-8")
    src = tmp_path / "CLAUDE.md"
    src.write_text("# new content", encoding="utf-8")
    merge_into_agents_md(tmp_path, [src], force=True)
    assert "new content" in (tmp_path / _AGENTS_MD).read_text(encoding="utf-8")


def test_merge_no_sources(tmp_path):
    actions = merge_into_agents_md(tmp_path, [])
    assert any("SKIP" in a for a in actions)
    assert not (tmp_path / _AGENTS_MD).exists()


def test_create_symlinks_replaces_real_files(tmp_path):
    agents_md = tmp_path / _AGENTS_MD
    agents_md.write_text("# agents", encoding="utf-8")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# claude", encoding="utf-8")
    actions = create_instruction_symlinks(tmp_path, [claude_md])
    assert claude_md.is_symlink()
    assert any("SYMLINK" in a for a in actions)


def test_create_symlinks_dry_run_does_not_modify(tmp_path):
    agents_md = tmp_path / _AGENTS_MD
    agents_md.write_text("# agents", encoding="utf-8")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# claude", encoding="utf-8")
    actions = create_instruction_symlinks(tmp_path, [claude_md], dry_run=True)
    assert not claude_md.is_symlink()
    assert claude_md.read_text(encoding="utf-8") == "# claude"
    assert any("SYMLINK" in a for a in actions)


def test_create_symlinks_skip_if_agents_md_missing(tmp_path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# claude", encoding="utf-8")
    actions = create_instruction_symlinks(tmp_path, [claude_md])
    assert any("SKIP" in a for a in actions)


def test_detect_skill_dirs_empty(tmp_path):
    assert detect_skill_dirs(tmp_path) == {}


def test_detect_skill_dirs_finds_real_dirs(tmp_path):
    skill_dir = tmp_path / ".agents" / "skills"
    skill_dir.mkdir(parents=True)
    result = detect_skill_dirs(tmp_path)
    assert ".agents/skills" in result


def test_detect_skill_dirs_skips_symlinks(tmp_path):
    canonical = tmp_path / ".claude" / "skills"
    canonical.mkdir(parents=True)
    agents_skills = tmp_path / ".agents" / "skills"
    agents_skills.parent.mkdir(parents=True)
    agents_skills.symlink_to(canonical)
    result = detect_skill_dirs(tmp_path)
    assert ".agents/skills" not in result


def test_detect_skill_dirs_excludes_canonical(tmp_path):
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    result = detect_skill_dirs(tmp_path)
    assert ".claude/skills" not in result


def test_consolidate_skills_moves_and_creates_symlink(tmp_path):
    agents_skills = tmp_path / ".agents" / "skills"
    agents_skills.mkdir(parents=True)
    (agents_skills / "my-skill").mkdir()
    (agents_skills / "my-skill" / "SKILL.md").write_text("# skill", encoding="utf-8")

    skill_dirs = {".agents/skills": agents_skills}
    actions = consolidate_skills(tmp_path, skill_dirs)

    canonical = tmp_path / _CANONICAL_SKILLS_DIR
    assert canonical.exists()
    assert (canonical / "my-skill" / "SKILL.md").exists()
    assert agents_skills.is_symlink()
    assert any("MOVE" in a for a in actions)
    assert any("SYMLINK" in a for a in actions)


def test_consolidate_skills_dry_run(tmp_path):
    agents_skills = tmp_path / ".agents" / "skills"
    agents_skills.mkdir(parents=True)
    (agents_skills / "skill-a").mkdir()

    skill_dirs = {".agents/skills": agents_skills}
    actions = consolidate_skills(tmp_path, skill_dirs, dry_run=True)

    assert not (tmp_path / _CANONICAL_SKILLS_DIR).exists()
    assert not agents_skills.is_symlink()
    assert any("MOVE" in a for a in actions)


def test_consolidate_skills_conflict_without_force(tmp_path):
    agents_skills = tmp_path / ".agents" / "skills"
    agents_skills.mkdir(parents=True)
    canonical = tmp_path / ".claude" / "skills"
    canonical.mkdir(parents=True)

    skill_dirs = {".agents/skills": agents_skills}
    actions = consolidate_skills(tmp_path, skill_dirs, force=False)
    assert any("SKIP" in a for a in actions)


def test_consolidate_skills_conflict_with_force(tmp_path):
    agents_skills = tmp_path / ".agents" / "skills"
    agents_skills.mkdir(parents=True)
    (agents_skills / "skill-b").mkdir()
    canonical = tmp_path / ".claude" / "skills"
    canonical.mkdir(parents=True)
    (canonical / "old-skill").mkdir()

    skill_dirs = {".agents/skills": agents_skills}
    actions = consolidate_skills(tmp_path, skill_dirs, force=True)
    assert any("MOVE" in a for a in actions)


def test_init_workspace_idempotent(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Claude", encoding="utf-8")
    init_workspace(tmp_path)
    init_workspace(tmp_path)
    assert (tmp_path / _AGENTS_MD).exists()


def test_init_workspace_dry_run_no_changes(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Claude", encoding="utf-8")
    actions = init_workspace(tmp_path, dry_run=True)
    assert not (tmp_path / _AGENTS_MD).exists()
    assert len(actions) > 0
