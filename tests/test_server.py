"""Tests for build_mcp — provider registration, scope flags, bundled skills, extra dirs."""

from fastmcp import Client

from agent_skill_router.server import _BUNDLED_SKILLS_PATH, _resolve_roots, build_mcp
from agent_skill_router.settings import ExtraDirectory

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
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = [str(r.uri) for r in resources]
        assert any("my-skill" in u for u in uris)


async def test_extra_dir_nonexistent_is_silently_skipped(all_disabled_settings, tmp_path):
    missing = tmp_path / "does-not-exist"
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=missing)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        assert resources == []


async def test_extra_dir_supporting_files_are_listed(all_disabled_settings, skill_dir_with_assets):
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir_with_assets)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = [str(r.uri) for r in resources]
        # supporting_files="resources" — reference.md must appear individually
        assert any("reference.md" in u for u in uris)
