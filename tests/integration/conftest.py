"""Fixtures for agent integration tests."""

import shutil
from pathlib import Path

import pytest

from agent_skill_router._skills import SkillEntry, discover_skills

_FIXTURES_WORKSPACE = Path(__file__).parent.parent / "fixtures" / "workspace"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy the fixture workspace into *tmp_path*, set it as cwd and fake home.

    Layout after copy::

        tmp_path/
          .vscode/mcp.json          ← github-copilot discover
          .opencode/mcp.json        ← opencode discover
          .opencode/commands/       ← opencode list_prompts
          .claude/mcp.json          ← claude discover
          .claude/commands/         ← claude list_prompts
          .cursor/mcp.json          ← cursor discover
          .cursor/rules/            ← cursor list_prompts
          .gemini/settings.json     ← gemini discover
          .gemini/commands/         ← gemini list_prompts (TOML + namespaced)
          .codex/config.toml        ← codex discover
          .codex/prompts/           ← codex list_prompts
          .goose/mcp.json           ← goose discover
          .goose/recipes/           ← goose list_prompts
          .github/prompts/          ← github-copilot list_prompts
          .agents/skills/           ← get_slash_commands source skills

    ``Path.home()`` is patched to ``tmp_path / "home"`` so user-scope paths
    point to an isolated directory that starts empty.
    """
    shutil.copytree(_FIXTURES_WORKSPACE, tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    return tmp_path


@pytest.fixture
def workspace_skills(workspace: Path) -> list[SkillEntry]:
    """Return SkillEntry list discovered from the fixture workspace skills dir."""
    skills_root = workspace / ".agents" / "skills"
    return discover_skills([skills_root])
