"""Integration tests for FastMCP prompt registration from native agent command files."""

from pathlib import Path
from typing import TYPE_CHECKING

from fastmcp import Client

from agent_skill_router.server import build_mcp
from agent_skill_router.settings import Settings

if TYPE_CHECKING:
    import pytest

_FIXTURE_PROMPT_NAMES = {
    "review-code",  # .github/prompts/review-code.prompt.md  (Copilot)
    "fix-bug",  # .claude/commands/fix-bug.md             (Claude)
    "create-pr",  # .opencode/commands/create-pr.md         (OpenCode)
    "typescript",  # .cursor/rules/typescript.mdc            (Cursor)
    "refactor",  # .gemini/commands/refactor.toml          (Gemini)
    "git:commit",  # .gemini/commands/git/commit.toml        (Gemini namespaced)
    "generate-tests",  # .codex/prompts/generate-tests.md        (Codex)
    "daily-standup",  # .goose/recipes/standup.yaml             (Goose)
}


async def test_all_fixture_agent_commands_registered(workspace: Path, all_disabled_settings: Settings) -> None:
    """Every native command file in the fixture workspace appears as an MCP prompt."""
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        names = {p.name for p in prompts}
        for expected in _FIXTURE_PROMPT_NAMES:
            assert expected in names, f"Expected prompt '{expected}' not found in {names}"


async def test_create_skill_always_present(workspace: Path, all_disabled_settings: Settings) -> None:
    """create-skill prompt is always registered regardless of workspace content."""
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        names = {p.name for p in prompts}
        assert "create-skill" in names


async def test_prompt_count_matches_fixture(workspace: Path, all_disabled_settings: Settings) -> None:
    """Total registered prompts = fixture commands + create-skill (no duplicates)."""
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        names = {p.name for p in prompts}
        expected = _FIXTURE_PROMPT_NAMES | {"create-skill"}
        assert names == expected


async def test_prompt_description_from_frontmatter(workspace: Path, all_disabled_settings: Settings) -> None:
    """Prompt descriptions come from the native file's frontmatter, not defaults."""
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        by_name = {p.name: p for p in prompts}
        assert "bug" in (by_name["fix-bug"].description or "").lower()
        assert "review" in (by_name["review-code"].description or "").lower()
        assert "pull request" in (by_name["create-pr"].description or "").lower()


async def test_prompt_content_matches_native_file_body(workspace: Path, all_disabled_settings: Settings) -> None:
    """Getting a prompt returns the body of the native command file (frontmatter stripped)."""
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        result = await client.get_prompt("fix-bug")
        assert result.messages
        text = result.messages[0].content.text  # type: ignore[union-attr]
        assert "bug" in text.lower()
        assert "---" not in text
        assert "allowed-tools" not in text


async def test_empty_workspace_registers_only_create_skill(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch", all_disabled_settings: Settings
) -> None:
    """No agent prompts are added when workspace has no native command files."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        names = {p.name for p in prompts}
        assert names == {"create-skill"}


async def test_first_provider_wins_on_name_collision(workspace: Path, all_disabled_settings: Settings) -> None:
    """When two agents define the same command name, the first provider's version is used."""
    duplicate = workspace / ".opencode" / "commands" / "fix-bug.md"
    duplicate.write_text("---\ndescription: OpenCode fix-bug override\n---\nOpenCode body.\n")

    mcp = build_mcp(all_disabled_settings)
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
        by_name = {p.name: p for p in prompts}
        assert "fix-bug" in by_name
        result = await client.get_prompt("fix-bug")
        text = result.messages[0].content.text  # type: ignore[union-attr]
        assert "OpenCode body" not in text
