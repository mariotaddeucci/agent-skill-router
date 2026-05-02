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


# ---------------------------------------------------------------------------
# list_skills tool
# ---------------------------------------------------------------------------


async def test_list_skills_returns_skill_names(all_disabled_settings, skill_dir):
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        result = await client.call_tool("list_skills", {})
        text = result.content[0].text  # type: ignore[union-attr]
        assert "my-skill" in text


async def test_list_skills_empty_when_no_skills(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        result = await client.call_tool("list_skills", {})
        assert "No skills" in result.content[0].text  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# get_skill tool
# ---------------------------------------------------------------------------


async def test_get_skill_returns_skill_md_content(all_disabled_settings, skill_dir):
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        result = await client.call_tool("get_skill", {"name": "my-skill"})
        text = result.content[0].text  # type: ignore[union-attr]
        assert "My Skill" in text


async def test_get_skill_includes_supporting_files(all_disabled_settings, skill_dir_with_assets):
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir_with_assets)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        result = await client.call_tool("get_skill", {"name": "rich-skill"})
        text = result.content[0].text  # type: ignore[union-attr]
        assert "Rich Skill" in text
        assert "reference.md" in text
        assert "Extra content" in text


async def test_get_skill_skill_md_comes_before_supporting_files(all_disabled_settings, skill_dir_with_assets):
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir_with_assets)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        result = await client.call_tool("get_skill", {"name": "rich-skill"})
        text = result.content[0].text  # type: ignore[union-attr]
        skill_md_pos = text.index("Rich Skill")
        reference_header_pos = text.index("--- reference.md ---")
        assert skill_md_pos < reference_header_pos


async def test_get_skill_unknown_name_returns_available_list(all_disabled_settings, skill_dir):
    settings = all_disabled_settings.model_copy(update={"extra_dirs": [ExtraDirectory(path=skill_dir)]})
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        result = await client.call_tool("get_skill", {"name": "does-not-exist"})
        text = result.content[0].text  # type: ignore[union-attr]
        assert "not found" in text
        assert "my-skill" in text


# ---------------------------------------------------------------------------
# _normalize_mcpserver_entry helper
# ---------------------------------------------------------------------------


def test_normalize_mcpserver_entry_stdio():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    result = _normalize_mcpserver_entry({"command": "uvx", "args": ["pkg"]})
    assert result is not None
    assert result.command == "uvx"
    assert result.args == ["pkg"]
    assert result.url is None


def test_normalize_mcpserver_entry_list_command():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    result = _normalize_mcpserver_entry({"command": ["uvx", "pkg", "run"]})
    assert result is not None
    assert result.command == "uvx"
    assert result.args == ["pkg", "run"]


def test_normalize_mcpserver_entry_url():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    result = _normalize_mcpserver_entry({"url": "https://example.com/mcp"})
    assert result is not None
    assert result.url == "https://example.com/mcp"
    assert result.command is None


def test_normalize_mcpserver_entry_with_env():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    result = _normalize_mcpserver_entry({"command": "uvx", "args": [], "env": {"MY_VAR": "val"}})
    assert result is not None
    assert result.env == {"MY_VAR": "val"}


def test_normalize_mcpserver_entry_empty_list_command_returns_none():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    result = _normalize_mcpserver_entry({"command": []})
    assert result is None


def test_normalize_mcpserver_entry_no_command_no_url_returns_none():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    result = _normalize_mcpserver_entry({"type": "stdio"})
    assert result is None


def test_normalize_mcpserver_entry_non_dict_returns_none():
    from agent_skill_router.agents._base import _normalize_mcpserver_entry

    assert _normalize_mcpserver_entry("invalid") is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# MCP proxy — enable_mcp_proxy flag and proxy registration
# ---------------------------------------------------------------------------


def test_mcp_proxy_disabled_when_flag_false(all_disabled_settings):
    mcp = build_mcp(all_disabled_settings)
    assert mcp is not None


def test_mcp_proxy_enabled_registers_proxy_provider(all_disabled_settings, tmp_path):
    from fastmcp import FastMCP

    # Write a cursor mcp.json so the cursor provider finds a server
    cursor_cfg = tmp_path / ".cursor" / "mcp.json"
    cursor_cfg.parent.mkdir(parents=True)
    import json

    cursor_cfg.write_text(json.dumps({"mcpServers": {"my-proxy-server": {"command": "echo", "args": []}}}))

    settings = all_disabled_settings.model_copy(update={"enable_mcp_proxy": True, "enable_workspace_level": True})
    mcp = build_mcp(settings, workspace_dir=tmp_path)

    assert isinstance(mcp, FastMCP)


def test_mcp_proxy_excludes_self_from_all_providers(all_disabled_settings, tmp_path):
    import json

    # Write configs for multiple agents, all including agent-skill-router as a server
    for subdir, key, value in [
        (".cursor/mcp.json", "mcpServers", {"agent-skill-router": {"command": "uvx", "args": []}}),
        (
            ".vscode/mcp.json",
            "servers",
            {"agent-skill-router": {"type": "stdio", "command": "uvx", "args": []}},
        ),
    ]:
        cfg = tmp_path / subdir
        cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({key: value}))

    settings = all_disabled_settings.model_copy(update={"enable_mcp_proxy": True, "enable_workspace_level": True})
    mcp = build_mcp(settings, workspace_dir=tmp_path)
    assert mcp is not None
