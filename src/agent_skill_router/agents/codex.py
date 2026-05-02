"""Codex (OpenAI CLI) MCP setup provider."""

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    AgentSetupProvider,
    McpConfig,
    PromptSlashCommand,
    SlashCommand,
    _parse_frontmatter,
)

if TYPE_CHECKING:
    from agent_skill_router._skills import SkillEntry


_TomlScalar = bool | int | str | list


def _toml_scalar(value: _TomlScalar) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    return "[" + ", ".join(_toml_scalar(v) for v in value) + "]"


def _serialize_toml(data: dict[str, _TomlScalar | dict]) -> str:
    """Minimal TOML serializer for a two-level config dict.

    Handles top-level scalars/lists first, then ``[section.key]`` tables for
    nested dicts.  Sufficient for Codex ``config.toml`` which has the shape::

        [mcp_servers.agent-skill-router]
        command = "uvx"
        args = ["--from", "..."]
    """
    lines: list[str] = []

    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}

    for key, value in scalars.items():
        lines.append(f"{key} = {_toml_scalar(value)}")
    if scalars:
        lines.append("")

    for outer_key, outer_val in tables.items():
        for inner_key, inner_val in outer_val.items():
            lines.append(f"[{outer_key}.{inner_key}]")
            for k, v in inner_val.items():
                lines.append(f"{k} = {_toml_scalar(v)}")
            lines.append("")

    return "\n".join(lines) + "\n"


class CodexSetupProvider(AgentSetupProvider):
    """Setup provider for Codex (OpenAI CLI).

    Config file format: ``config.toml``

    Workspace scope: ``<cwd>/.codex/config.toml``
    User scope:      ``~/.codex/config.toml``

    Discovery: searches both paths and returns whichever exist.

    Install: merges the MCP server entry under ``[mcp_servers.agent-skill-router]``
    using the Codex TOML schema (``command``, ``args``). Existing entries are
    left untouched; the agent-skill-router section is added or updated
    idempotently.

    Prompts: reads custom prompts from ``.codex/prompts/*.md`` files.
    """

    name = "codex"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".codex" / "config.toml"

    def config_path_user(self) -> Path:
        return Path.home() / ".codex" / "config.toml"

    def discover(self) -> list[Path]:
        """Return every ``config.toml`` that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``[mcp_servers.agent-skill-router]``::

            [mcp_servers.agent-skill-router]
            command = "uvx"
            args = ["--from", "..."]
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.exists():
            try:
                data: dict = tomllib.loads(config_path.read_text(encoding="utf-8"))
            except (tomllib.TOMLDecodeError, OSError):
                data = {}
        else:
            data = {}

        mcp_servers: dict = data.setdefault("mcp_servers", {})
        mcp_servers["agent-skill-router"] = {
            "command": mcp_config.command,
            "args": list(mcp_config.args),
        }

        config_path.write_text(_serialize_toml(data), encoding="utf-8")

    def get_slash_commands(self, skills: list["SkillEntry"]) -> list[SlashCommand]:
        """Convert skills into Codex slash commands (prompts)."""
        commands: list[SlashCommand] = []
        for skill in skills:
            skill_md = skill.directory / "SKILL.md"
            if not skill_md.exists():
                continue
            commands.append(
                PromptSlashCommand(
                    name=f"/{skill.name}",
                    description=skill.description,
                    prompt=skill_md.read_text(encoding="utf-8"),
                )
            )
        return commands

    def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]:
        seen: set[str] = set()
        commands: list[SlashCommand] = []
        for root in roots or [Path.cwd()]:
            prompts_dir = root / ".codex" / "prompts"
            if not prompts_dir.is_dir():
                continue
            for path in sorted(prompts_dir.glob("*.md")):
                if path.stem in seen:
                    continue
                seen.add(path.stem)
                content = path.read_text(encoding="utf-8")
                meta, body = _parse_frontmatter(content)
                commands.append(
                    PromptSlashCommand(
                        name=f"/{path.stem}",
                        description=meta.get("description", ""),
                        prompt=body,
                    )
                )
        return commands
