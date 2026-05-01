"""Tests for the create-skill MCP prompt."""

from pathlib import Path

import pytest
from fastmcp import Client

from agent_skill_router.server import build_mcp
from agent_skill_router.settings import Settings


async def _get_prompt_text(mcp, goal: str, save_to_user_level: bool = False) -> str:
    async with Client(mcp) as client:
        result = await client.get_prompt(
            "create-skill",
            {"goal": goal, "save_to_user_level": save_to_user_level},
        )
        return result.messages[0].content.text


# ---------------------------------------------------------------------------
# Prompt registration
# ---------------------------------------------------------------------------


async def test_create_skill_prompt_is_registered(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        assert any(p.name == "create-skill" for p in prompts)


async def test_create_skill_prompt_has_description(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        prompt = next(p for p in prompts if p.name == "create-skill")
        assert prompt.description
        assert len(prompt.description) > 0


# ---------------------------------------------------------------------------
# Prompt content — workspace (default)
# ---------------------------------------------------------------------------


async def test_prompt_contains_goal(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "process PDFs and extract tables")
    assert "process PDFs and extract tables" in text


async def test_prompt_default_points_to_workspace_agents(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something")
    assert ".agents/skills" in text
    # workspace path contains cwd fragment, not home
    assert str(Path.cwd()) in text


async def test_prompt_mentions_skill_creator(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something")
    assert "skill-creator" in text


async def test_prompt_explains_what_a_skill_is(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something")
    assert "SKILL.md" in text


async def test_prompt_workspace_scope_note(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something", save_to_user_level=False)
    assert "this workspace only" in text


async def test_prompt_directory_already_created(all_disabled_settings, tmp_path, monkeypatch):
    # Redirect cwd so we don't pollute the real workspace during tests
    monkeypatch.chdir(tmp_path)
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something")
    created = tmp_path / ".agents" / "skills"
    assert created.exists()
    assert "already been created" in text


# ---------------------------------------------------------------------------
# Prompt content — user level
# ---------------------------------------------------------------------------


async def test_prompt_user_level_points_to_home_agents(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something", save_to_user_level=True)
    assert str(Path.home() / ".agents" / "skills") in text


async def test_prompt_user_level_scope_note(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    text = await _get_prompt_text(mcp, "something", save_to_user_level=True)
    assert "all workspaces" in text


async def test_prompt_user_level_creates_directory(all_disabled_settings, tmp_path, monkeypatch):
    # Patch Path.home to a tmp dir so we don't create real ~/.agents/skills in CI
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    mcp = build_mcp(all_disabled_settings)
    await _get_prompt_text(mcp, "something", save_to_user_level=True)
    assert (fake_home / ".agents" / "skills").exists()


# ---------------------------------------------------------------------------
# Prompt — both workspace and user level create distinct directories
# ---------------------------------------------------------------------------


async def test_prompt_workspace_and_user_level_create_different_dirs(
    all_disabled_settings, tmp_path, monkeypatch
):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    mcp = build_mcp(all_disabled_settings)

    await _get_prompt_text(mcp, "skill A", save_to_user_level=False)
    await _get_prompt_text(mcp, "skill B", save_to_user_level=True)

    assert (tmp_path / ".agents" / "skills").exists()
    assert (fake_home / ".agents" / "skills").exists()
