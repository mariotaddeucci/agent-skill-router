"""Gemini CLI MCP setup provider."""

import json
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    AgentSetupProvider,
    McpConfig,
    PromptSlashCommand,
    SlashCommand,
)

if TYPE_CHECKING:
    from agent_skill_router._skills import SkillEntry


class GeminiSetupProvider(AgentSetupProvider):
    """Setup provider for Gemini CLI.

    Config file format: ``.gemini/settings.json``

    Workspace scope: ``<cwd>/.gemini/settings.json``
    User scope:      ``~/.gemini/settings.json``

    Discovery: searches both paths and returns whichever exist.

    Install: merges the MCP server entry under ``mcpServers.<name>`` using the
    Gemini CLI MCP schema (``command``, ``args``). Existing entries are left
    untouched; the agent-skill-router entry is added or updated idempotently.

    Prompts: reads custom prompts from ``.gemini/prompts/*.md`` files.
    """

    name = "gemini"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".gemini" / "settings.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".gemini" / "settings.json"

    def discover(self) -> list[Path]:
        """Return every ``settings.json`` that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``mcpServers.agent-skill-router``::

            {
              "mcpServers": {
                "agent-skill-router": {
                  "command": "...",
                  "args": [...]
                }
              }
            }
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.exists():
            try:
                data: dict = json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}

        servers: dict = data.setdefault("mcpServers", {})
        servers["agent-skill-router"] = {
            "command": mcp_config.command,
            "args": mcp_config.args,
        }

        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get_slash_commands(self, skills: list["SkillEntry"]) -> list[SlashCommand]:
        """Convert skills into Gemini CLI slash commands (prompts)."""
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
            commands_dir = root / ".gemini" / "commands"
            if not commands_dir.is_dir():
                continue
            for path in sorted(commands_dir.rglob("*.toml")):
                try:
                    data = tomllib.loads(path.read_text(encoding="utf-8"))
                except (tomllib.TOMLDecodeError, OSError):
                    continue

                rel = path.relative_to(commands_dir)
                parts = list(rel.parts)
                parts[-1] = parts[-1].removesuffix(".toml")
                name = ":".join(parts)

                if name in seen:
                    continue
                seen.add(name)
                commands.append(
                    PromptSlashCommand(
                        name=f"/{name}",
                        description=data.get("description", ""),
                        prompt=data.get("prompt", ""),
                    )
                )
        return commands
