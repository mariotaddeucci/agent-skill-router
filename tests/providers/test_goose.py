"""Tests for the Goose provider scope flags."""

import agent_skill_router.server as srv
from fastmcp import Client
from fastmcp.server.providers.skills import GooseSkillsProvider, SkillsDirectoryProvider

from agent_skill_router.server import build_mcp


async def test_goose_provider_workspace_root_used(all_disabled_settings, tmp_path):
    ws = tmp_path / ".goose" / "skills"
    skill = ws / "ws-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: ws\n---\n# WS\n")

    settings = all_disabled_settings.model_copy(
        update={
            "enable_goose": True,
            "enable_workspace_level": True,
            "enable_user_level": False,
        }
    )

    original = srv._PROVIDER_ROOTS
    patched = [
        (attr, cls, roots)
        if attr != "enable_goose"
        else (
            "enable_goose",
            SkillsDirectoryProvider,
            {
                "workspace": [ws],
                "user": [tmp_path / ".config" / "agents" / "user-skills"],
            },
        )
        for attr, cls, roots in original
    ]
    srv._PROVIDER_ROOTS = patched  # type: ignore[assignment]
    try:
        mcp = build_mcp(settings)
        async with Client(mcp) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert any("ws-skill" in u for u in uris)
    finally:
        srv._PROVIDER_ROOTS = original  # type: ignore[assignment]


async def test_goose_provider_user_root_used(all_disabled_settings, tmp_path):
    user = tmp_path / ".config" / "agents" / "skills"
    skill = user / "user-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: user\n---\n# User\n")

    settings = all_disabled_settings.model_copy(
        update={
            "enable_goose": True,
            "enable_workspace_level": False,
            "enable_user_level": True,
        }
    )

    original = srv._PROVIDER_ROOTS
    patched = [
        (attr, cls, roots)
        if attr != "enable_goose"
        else (
            "enable_goose",
            SkillsDirectoryProvider,
            {
                "workspace": [tmp_path / ".goose" / "ws-skills"],
                "user": [user],
            },
        )
        for attr, cls, roots in original
    ]
    srv._PROVIDER_ROOTS = patched  # type: ignore[assignment]
    try:
        mcp = build_mcp(settings)
        async with Client(mcp) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert any("user-skill" in u for u in uris)
    finally:
        srv._PROVIDER_ROOTS = original  # type: ignore[assignment]


async def test_goose_provider_disabled_exposes_nothing(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        assert resources == []


def test_goose_provider_class_registered():
    """Ensure the Goose entry in _PROVIDER_ROOTS uses GooseSkillsProvider."""
    entry = next(e for e in srv._PROVIDER_ROOTS if e[0] == "enable_goose")
    assert entry[1] is GooseSkillsProvider
