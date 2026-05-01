"""Integration tests for AgentSetupProvider.list_prompts()."""

from pathlib import Path

import pytest

from agent_skill_router.agents._base import PromptSlashCommand
from agent_skill_router.agents.claude import ClaudeSetupProvider
from agent_skill_router.agents.codex import CodexSetupProvider
from agent_skill_router.agents.cursor import CursorSetupProvider
from agent_skill_router.agents.gemini import GeminiSetupProvider
from agent_skill_router.agents.github_copilot import GitHubCopilotSetupProvider
from agent_skill_router.agents.goose import GooseSetupProvider
from agent_skill_router.agents.opencode import OpenCodeSetupProvider


def test_list_prompts_returns_empty_in_clean_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All providers return [] when no prompt files exist."""
    monkeypatch.chdir(tmp_path)
    from agent_skill_router.agents import AGENT_PROVIDERS

    for name, provider in AGENT_PROVIDERS.items():
        result = provider.list_prompts(root=tmp_path)
        assert result == [], f"{name}: expected [] in empty workspace, got {result}"


class TestGitHubCopilotListPrompts:
    """GitHub Copilot reads .github/prompts/*.prompt.md"""

    def setup_method(self) -> None:
        self.provider = GitHubCopilotSetupProvider()

    def test_reads_prompt_md_file(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 1

    def test_command_name_strips_prompt_suffix(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].name == "/review-code"

    def test_description_from_frontmatter(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].description == "Review selected code for quality and bugs"

    def test_prompt_body_is_markdown_content(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert "review" in result[0].prompt.lower()

    def test_returns_prompt_slash_command_type(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert result[0].type == "prompt"


class TestOpenCodeListPrompts:
    """OpenCode reads .opencode/commands/*.md"""

    def setup_method(self) -> None:
        self.provider = OpenCodeSetupProvider()

    def test_reads_command_md_file(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 1

    def test_command_name_from_stem(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].name == "/create-pr"

    def test_description_from_frontmatter(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert "pull request" in result[0].description.lower()

    def test_prompt_body_present(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert len(result[0].prompt) > 0


class TestClaudeListPrompts:
    """Claude reads .claude/commands/*.md"""

    def setup_method(self) -> None:
        self.provider = ClaudeSetupProvider()

    def test_reads_command_md_file(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 1

    def test_command_name_from_stem(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].name == "/fix-bug"

    def test_description_from_frontmatter(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert "bug" in result[0].description.lower()

    def test_prompt_body_present(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert len(result[0].prompt) > 0

    def test_frontmatter_not_in_prompt_body(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert "allowed-tools" not in result[0].prompt
        assert "---" not in result[0].prompt


class TestCursorListPrompts:
    """Cursor reads .cursor/rules/*.mdc"""

    def setup_method(self) -> None:
        self.provider = CursorSetupProvider()

    def test_reads_mdc_file(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 1

    def test_command_name_from_stem(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].name == "/typescript"

    def test_description_from_frontmatter(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert "typescript" in result[0].description.lower()

    def test_prompt_body_is_rule_content(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert "TypeScript" in result[0].prompt

    def test_frontmatter_fields_not_in_prompt(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert "globs" not in result[0].prompt
        assert "alwaysApply" not in result[0].prompt

    def test_also_reads_md_extension(self, workspace: Path) -> None:
        md_file = workspace / ".cursor" / "rules" / "extra.md"
        md_file.write_text("---\ndescription: Extra rule\n---\nExtra rule content.\n")
        result = self.provider.list_prompts(root=workspace)
        names = [r.name for r in result]
        assert "/extra" in names
        assert "/typescript" in names


class TestGeminiListPrompts:
    """Gemini reads .gemini/commands/*.toml with namespace support."""

    def setup_method(self) -> None:
        self.provider = GeminiSetupProvider()

    def test_reads_toml_file(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 2  # refactor.toml + git/commit.toml

    def test_root_command_name(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        names = [r.name for r in result]
        assert "/refactor" in names

    def test_namespaced_command_uses_colon(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        names = [r.name for r in result]
        assert "/git:commit" in names

    def test_description_from_toml_field(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        refactor = next(r for r in result if r.name == "/refactor")
        assert "pure function" in refactor.description.lower()

    def test_prompt_from_toml_field(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        refactor = next(r for r in result if r.name == "/refactor")
        assert isinstance(refactor, PromptSlashCommand)
        assert len(refactor.prompt) > 0
        assert "pure function" in refactor.prompt.lower()


class TestCodexListPrompts:
    """Codex reads .codex/prompts/*.md (legacy format)."""

    def setup_method(self) -> None:
        self.provider = CodexSetupProvider()

    def test_reads_md_file(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 1

    def test_command_name_from_stem(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].name == "/generate-tests"

    def test_description_from_frontmatter(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert "test" in result[0].description.lower()

    def test_prompt_body_present(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert len(result[0].prompt) > 0


class TestGooseListPrompts:
    """Goose reads .goose/recipes/*.yaml with YAML parser."""

    def setup_method(self) -> None:
        self.provider = GooseSetupProvider()

    def test_reads_yaml_recipe(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert len(result) == 1

    def test_command_name_from_title_field(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert result[0].name == "/daily-standup"

    def test_description_from_yaml_field(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert "standup" in result[0].description.lower()

    def test_prompt_from_instructions_block(self, workspace: Path) -> None:
        result = self.provider.list_prompts(root=workspace)
        assert isinstance(result[0], PromptSlashCommand)
        assert "git commits" in result[0].prompt.lower()

    def test_fallback_to_filename_when_no_title(self, workspace: Path) -> None:
        recipe = workspace / ".goose" / "recipes" / "no-title.yaml"
        recipe.write_text("version: '1.0.0'\ndescription: No title recipe\ninstructions: Do something.\n")
        result = self.provider.list_prompts(root=workspace)
        names = [r.name for r in result]
        assert "/no-title" in names

    def test_prompt_falls_back_to_prompt_field(self, workspace: Path) -> None:
        recipe = workspace / ".goose" / "recipes" / "prompt-field.yaml"
        recipe.write_text(
            "version: '1.0.0'\ntitle: prompt-field\ndescription: Uses prompt field\nprompt: Prompt body here.\n"
        )
        result = self.provider.list_prompts(root=workspace)
        pf = next(r for r in result if r.name == "/prompt-field")
        assert isinstance(pf, PromptSlashCommand)
        assert pf.prompt == "Prompt body here."
