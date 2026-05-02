"""OpenCode MCP setup provider."""

import json
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


class OpenCodeSetupProvider(AgentSetupProvider):
    """Setup provider for OpenCode.

    Workspace: ``<cwd>/.opencode/mcp.json``
    User:      ``~/.config/opencode/opencode.json``

    Discovery: searches both paths and returns whichever exist.

    Install: merges the MCP server entry under ``mcp.<name>`` using the
    OpenCode-compatible schema (``type``, ``command``, ``enabled``).
    Existing entries are left untouched; the agent-skill-router entry is
    added or updated idempotently.
    """

    name = "opencode"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".opencode" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".config" / "opencode" / "opencode.json"

    def discover(self) -> list[Path]:
        """Return every config path that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``mcp.agent-skill-router`` using the
        OpenCode MCP schema::

            {
              "mcp": {
                "agent-skill-router": {
                  "type": "local",
                  "command": ["uvx", ...],
                  "enabled": true
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

        mcp: dict = data.setdefault("mcp", {})
        mcp["agent-skill-router"] = {
            "type": "local",
            "command": [mcp_config.command, *mcp_config.args],
            "enabled": True,
        }

        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get_slash_commands(self, skills: list["SkillEntry"]) -> list[SlashCommand]:
        """Convert skills into OpenCode slash commands (prompts)."""
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
            commands_dir = root / ".opencode" / "commands"
            if not commands_dir.is_dir():
                continue
            for path in sorted(commands_dir.glob("*.md")):
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
