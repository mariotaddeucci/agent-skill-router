"""Shared fixtures for agent-skill-router tests."""

import pytest

from agent_skill_router.settings import Settings


@pytest.fixture
def all_disabled_settings(tmp_path):
    """Settings with every provider disabled — clean baseline."""
    return Settings(
        enable_workspace_level=False,
        enable_user_level=False,
        enable_bundled=False,
        enable_claude=False,
        enable_cursor=False,
        enable_vscode=False,
        enable_codex=False,
        enable_gemini=False,
        enable_goose=False,
        enable_github_copilot=False,
        enable_opencode=False,
        enable_agents=False,
        enable_openclaw=False,
    )


@pytest.fixture
def skill_dir(tmp_path):
    """Create a minimal valid skill directory with a SKILL.md file."""
    skill = tmp_path / "my-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\ndescription: Test skill\n---\n# My Skill\nDoes something useful.\n")
    return tmp_path


@pytest.fixture
def skill_dir_with_assets(tmp_path):
    """Create a skill directory that also has supporting files."""
    skill = tmp_path / "rich-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\ndescription: Rich skill\n---\n# Rich Skill\nSee reference.md.\n")
    (skill / "reference.md").write_text("# Reference\nExtra content.\n")
    sub = skill / "examples"
    sub.mkdir()
    (sub / "sample.txt").write_text("example file\n")
    return tmp_path
