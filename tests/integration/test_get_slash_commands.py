"""Integration tests for AgentSetupProvider.get_slash_commands()."""

from pathlib import Path

from agent_skill_router._skills import SkillEntry
from agent_skill_router.agents import AGENT_PROVIDERS
from agent_skill_router.agents._base import PromptSlashCommand


def test_get_slash_commands_empty_without_skills(workspace: Path) -> None:
    """All providers return [] when skills list is empty."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.get_slash_commands([])
        assert result == [], f"{name}: expected [] for empty skills list"


def test_get_slash_commands_returns_list(workspace_skills: list[SkillEntry]) -> None:
    """All providers return a list from get_slash_commands."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.get_slash_commands(workspace_skills)
        assert isinstance(result, list), f"{name}: must return list"


def test_get_slash_commands_count_matches_skills(workspace_skills: list[SkillEntry]) -> None:
    """Each provider generates one command per skill that has SKILL.md."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.get_slash_commands(workspace_skills)
        assert len(result) == len(workspace_skills), (
            f"{name}: expected {len(workspace_skills)} commands, got {len(result)}"
        )


def test_get_slash_commands_all_are_prompt_type(workspace_skills: list[SkillEntry]) -> None:
    """All generated slash commands are PromptSlashCommand with type='prompt'."""
    for name, provider in AGENT_PROVIDERS.items():
        for cmd in provider.get_slash_commands(workspace_skills):
            assert isinstance(cmd, PromptSlashCommand), f"{name}: expected PromptSlashCommand, got {type(cmd)}"
            assert cmd.type == "prompt"


def test_get_slash_commands_names_have_slash_prefix(workspace_skills: list[SkillEntry]) -> None:
    """Every generated command name starts with '/'."""
    for name, provider in AGENT_PROVIDERS.items():
        for cmd in provider.get_slash_commands(workspace_skills):
            assert cmd.name.startswith("/"), f"{name}: command name '{cmd.name}' must start with '/'"


def test_get_slash_commands_names_match_skill_names(workspace_skills: list[SkillEntry]) -> None:
    """Command names match /<skill.name> for every skill."""
    skill_names = {f"/{s.name}" for s in workspace_skills}
    for name, provider in AGENT_PROVIDERS.items():
        result_names = {cmd.name for cmd in provider.get_slash_commands(workspace_skills)}
        assert result_names == skill_names, f"{name}: command names {result_names} don't match expected {skill_names}"


def test_get_slash_commands_description_from_skill(workspace_skills: list[SkillEntry]) -> None:
    """Command description comes from the SkillEntry description."""
    for name, provider in AGENT_PROVIDERS.items():
        for cmd in provider.get_slash_commands(workspace_skills):
            skill = next(s for s in workspace_skills if f"/{s.name}" == cmd.name)
            assert cmd.description == skill.description, f"{name}/{cmd.name}: description mismatch"


def test_get_slash_commands_prompt_contains_skill_md_content(
    workspace_skills: list[SkillEntry],
) -> None:
    """Command prompt is the full content of the skill's SKILL.md file."""
    for name, provider in AGENT_PROVIDERS.items():
        for cmd in provider.get_slash_commands(workspace_skills):
            skill = next(s for s in workspace_skills if f"/{s.name}" == cmd.name)
            expected = (skill.directory / "SKILL.md").read_text(encoding="utf-8")
            assert isinstance(cmd, PromptSlashCommand)
            assert cmd.prompt == expected, f"{name}/{cmd.name}: prompt content mismatch"


def test_get_slash_commands_skips_skill_without_skill_md(workspace: Path) -> None:
    """Skills without SKILL.md are silently skipped."""
    no_md_dir = workspace / ".agents" / "skills" / "no-skill-md"
    no_md_dir.mkdir(parents=True)
    (no_md_dir / "README.md").write_text("Not a SKILL.md")

    broken_skill = SkillEntry(
        name="no-skill-md",
        description="Missing SKILL.md",
        directory=no_md_dir,
    )

    for name, provider in AGENT_PROVIDERS.items():
        result = provider.get_slash_commands([broken_skill])
        assert result == [], f"{name}: should skip skill without SKILL.md"


def test_get_slash_commands_cross_agent_consistency(workspace_skills: list[SkillEntry]) -> None:
    """All providers generate the same logical set of commands from the same skills."""
    all_results = {name: provider.get_slash_commands(workspace_skills) for name, provider in AGENT_PROVIDERS.items()}

    first_name, first_cmds = next(iter(all_results.items()))
    first_names = {c.name for c in first_cmds}
    first_descriptions = {c.name: c.description for c in first_cmds}
    first_prompts = {c.name: c.prompt for c in first_cmds if isinstance(c, PromptSlashCommand)}

    for name, cmds in all_results.items():
        names = {c.name for c in cmds}
        assert names == first_names, f"Command names differ between {first_name} and {name}"
        for cmd in cmds:
            assert cmd.description == first_descriptions[cmd.name], (
                f"{name}/{cmd.name}: description differs from {first_name}"
            )
            assert isinstance(cmd, PromptSlashCommand)
            assert cmd.prompt == first_prompts[cmd.name], f"{name}/{cmd.name}: prompt differs from {first_name}"
