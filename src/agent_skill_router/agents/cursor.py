"""Cursor MCP setup provider."""

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


class CursorSetupProvider(AgentSetupProvider):
    """Setup provider for Cursor.

    Config file format: ``.cursor/mcp.json``

    Workspace scope: ``<cwd>/.cursor/mcp.json``
    User scope:      ``~/.cursor/mcp.json``

    Discovery: searches both paths and returns whichever exist.

    Install: merges the MCP server entry under ``mcpServers.<name>`` using the
    Cursor MCP schema (``command``, ``args`` — no ``type`` field). Existing
    entries are left untouched; the agent-skill-router entry is added or updated
    idempotently.

    Prompts: reads custom prompts from ``.cursor/prompts/*.md`` files.
    """

    name = "cursor"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".cursor" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".cursor" / "mcp.json"

    def discover(self) -> list[Path]:
        """Return every ``mcp.json`` that already exists on this machine."""
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
        """Convert skills into Cursor slash commands (prompts)."""
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

    def list_prompts(self, root: Path | None = None) -> list[SlashCommand]:
        """Read rules from ``.cursor/rules/`` under *root*.

        Cursor stores custom rules/prompts as ``.mdc`` (or ``.md``) files under
        ``.cursor/rules/``.  Each file may contain YAML frontmatter with a
        ``description`` key; the body is the rule content.

        Example file (``.cursor/rules/style.mdc``)::

            ---
            description: Enforce project code style conventions
            globs: "src/**/*.ts"
            alwaysApply: false
            ---
            Use functional components with hooks...
        """
        rules_dir = (root or Path.cwd()) / ".cursor" / "rules"
        if not rules_dir.is_dir():
            return []

        commands: list[SlashCommand] = []
        for path in sorted(rules_dir.glob("*.mdc")) + sorted(rules_dir.glob("*.md")):
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
