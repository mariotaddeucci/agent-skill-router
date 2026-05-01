"""Tests for build_mcp — provider registration, scope flags, bundled skills, extra dirs."""

import pytest
from fastmcp import Client

from agent_skill_router.server import _BUNDLED_SKILLS_PATH, _resolve_roots, build_mcp
from agent_skill_router.settings import ExtraDirectory, Settings


# ---------------------------------------------------------------------------
# _resolve_roots unit tests (pure, no I/O)
# ---------------------------------------------------------------------------


def test_resolve_roots_both_levels_existing(tmp_path):
    ws = tmp_path / "workspace"
    user = tmp_path / "user"
    ws.mkdir()
    user.mkdir()
    roots = _resolve_roots({"workspace": [ws], "user": [user]}, True, True)
    assert ws in roots
    assert user in roots


def test_resolve_roots_workspace_only(tmp_path):
    ws = tmp_path / "workspace"
    user = tmp_path / "user"
    ws.mkdir()
    user.mkdir()
    roots = _resolve_roots({"workspace": [ws], "user": [user]}, True, False)
    assert ws in roots
    assert user not in roots


def test_resolve_roots_user_only(tmp_path):
    ws = tmp_path / "workspace"
    user = tmp_path / "user"
    ws.mkdir()
    user.mkdir()
    roots = _resolve_roots({"workspace": [ws], "user": [user]}, False, True)
    assert ws not in roots
    assert user in roots


def test_resolve_roots_nonexistent_paths_excluded(tmp_path):
    missing = tmp_path / "does-not-exist"
    roots = _resolve_roots({"user": [missing]}, True, True)
    assert roots == []


def test_resolve_roots_both_disabled(tmp_path):
    ws = tmp_path / "workspace"
    user = tmp_path / "user"
    ws.mkdir()
    user.mkdir()
    roots = _resolve_roots({"workspace": [ws], "user": [user]}, False, False)
    assert roots == []


# ---------------------------------------------------------------------------
# build_mcp — basic structure
# ---------------------------------------------------------------------------


def test_build_mcp_returns_fastmcp_instance(all_disabled_settings):
    from fastmcp import FastMCP
    mcp = build_mcp(all_disabled_settings)
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "Agent Skill Router"


def test_build_mcp_uses_default_settings_when_none():
    # Should not raise even when no settings provided
    mcp = build_mcp(None)
    from fastmcp import FastMCP
    assert isinstance(mcp, FastMCP)


async def test_mcp_always_has_create_skill_prompt(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        names = [p.name for p in prompts]
        assert "create-skill" in names


# ---------------------------------------------------------------------------
# Bundled skills
# ---------------------------------------------------------------------------


def test_bundled_skills_path_exists():
    assert _BUNDLED_SKILLS_PATH.exists()
    assert _BUNDLED_SKILLS_PATH.is_dir()


def test_bundled_skills_contains_skill_creator():
    skill = _BUNDLED_SKILLS_PATH / "skill-creator" / "SKILL.md"
    assert skill.exists()


async def test_bundled_skills_exposed_as_resources(all_disabled_settings):
    settings = all_disabled_settings.model_copy(update={"enable_bundled": True})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = [str(r.uri) for r in resources]
        assert any("skill-creator" in u for u in uris)


async def test_bundled_skills_disabled_exposes_no_resources(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)  # enable_bundled=False
    async with Client(mcp) as client:
        resources = await client.list_resources()
        assert resources == []


# ---------------------------------------------------------------------------
# Extra directories
# ---------------------------------------------------------------------------


async def test_extra_dir_skill_is_exposed(all_disabled_settings, skill_dir):
    settings = all_disabled_settings.model_copy(
        update={"extra_dirs": [ExtraDirectory(path=skill_dir)]}
    )
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = [str(r.uri) for r in resources]
        assert any("my-skill" in u for u in uris)


async def test_extra_dir_nonexistent_is_silently_skipped(all_disabled_settings, tmp_path):
    missing = tmp_path / "does-not-exist"
    settings = all_disabled_settings.model_copy(
        update={"extra_dirs": [ExtraDirectory(path=missing)]}
    )
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        assert resources == []


async def test_extra_dir_supporting_files_are_listed(all_disabled_settings, skill_dir_with_assets):
    settings = all_disabled_settings.model_copy(
        update={"extra_dirs": [ExtraDirectory(path=skill_dir_with_assets)]}
    )
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = [str(r.uri) for r in resources]
        # supporting_files="resources" — reference.md must appear individually
        assert any("reference.md" in u for u in uris)


# ---------------------------------------------------------------------------
# Scope flags — agents provider (has both workspace + user roots)
# ---------------------------------------------------------------------------


async def test_agents_provider_workspace_root_used(all_disabled_settings, tmp_path):
    agents_ws = tmp_path / ".agents" / "skills"
    skill = agents_ws / "ws-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: ws\n---\n# WS\n")

    settings = all_disabled_settings.model_copy(update={
        "enable_agents": True,
        "enable_workspace_level": True,
        "enable_user_level": False,
    })

    # Patch cwd so the provider sees our tmp workspace
    import agent_skill_router.server as srv
    original = srv._PROVIDER_ROOTS

    from pathlib import Path
    from typing import Literal
    from fastmcp.server.providers.skills import SkillsDirectoryProvider

    patched = [
        (attr, cls, roots) if attr != "enable_agents" else
        ("enable_agents", SkillsDirectoryProvider, {
            "workspace": [agents_ws],
            "user": [tmp_path / ".agents" / "user-skills"],  # doesn't exist
        })
        for attr, cls, roots in original
    ]
    srv._PROVIDER_ROOTS = patched
    try:
        mcp = build_mcp(settings)
        async with Client(mcp) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert any("ws-skill" in u for u in uris)
    finally:
        srv._PROVIDER_ROOTS = original


async def test_agents_provider_user_root_used(all_disabled_settings, tmp_path):
    agents_user = tmp_path / ".agents" / "user-skills"
    skill = agents_user / "user-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: user\n---\n# User\n")

    settings = all_disabled_settings.model_copy(update={
        "enable_agents": True,
        "enable_workspace_level": False,
        "enable_user_level": True,
    })

    import agent_skill_router.server as srv
    from fastmcp.server.providers.skills import SkillsDirectoryProvider

    original = srv._PROVIDER_ROOTS
    patched = [
        (attr, cls, roots) if attr != "enable_agents" else
        ("enable_agents", SkillsDirectoryProvider, {
            "workspace": [tmp_path / ".agents" / "ws-skills"],  # doesn't exist
            "user": [agents_user],
        })
        for attr, cls, roots in original
    ]
    srv._PROVIDER_ROOTS = patched
    try:
        mcp = build_mcp(settings)
        async with Client(mcp) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert any("user-skill" in u for u in uris)
    finally:
        srv._PROVIDER_ROOTS = original


async def test_agents_provider_disabled_exposes_nothing(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        assert resources == []


# ---------------------------------------------------------------------------
# OpenClaw provider
# ---------------------------------------------------------------------------


async def test_openclaw_provider_exposes_skills(all_disabled_settings, tmp_path):
    openclaw = tmp_path / ".openclaw" / "skills"
    skill = openclaw / "claw-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: claw\n---\n# Claw\n")

    settings = all_disabled_settings.model_copy(update={
        "enable_openclaw": True,
        "enable_user_level": True,
    })

    import agent_skill_router.server as srv
    from fastmcp.server.providers.skills import SkillsDirectoryProvider

    original = srv._PROVIDER_ROOTS
    patched = [
        (attr, cls, roots) if attr != "enable_openclaw" else
        ("enable_openclaw", SkillsDirectoryProvider, {"user": [openclaw]})
        for attr, cls, roots in original
    ]
    srv._PROVIDER_ROOTS = patched
    try:
        mcp = build_mcp(settings)
        async with Client(mcp) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert any("claw-skill" in u for u in uris)
    finally:
        srv._PROVIDER_ROOTS = original
