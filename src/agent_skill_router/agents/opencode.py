"""OpenCode MCP setup provider."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    _SELF_SERVER_NAME,
    AgentSetupProvider,
    McpConfig,
    NormalizedMcpServer,
    PromptSlashCommand,
    SlashCommand,
    _normalize_mcpserver_entry,
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
        """Return the path to the OpenCode MCP config file for workspace-level installation.

        Returns:
            Path — ``<cwd>/.opencode/mcp.json``
        """
        return Path.cwd() / ".opencode" / "mcp.json"

    def config_path_user(self) -> Path:
        """Return the path to the OpenCode MCP config file for user-level installation.

        Returns:
            Path — ``~/.config/opencode/opencode.json``
        """
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
        """Scan ``.opencode/commands/*.md`` under each root for slash command definitions.

        Args:
            roots: List of base directories to scan.  Defaults to ``[Path.cwd()]``
                when *None*.

        Returns:
            List of :class:`SlashCommand` objects discovered, de-duplicated by stem.
        """
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

    def read_mcp_servers(self, roots: list[Path] | None = None) -> dict[str, NormalizedMcpServer]:
        """Read MCP server entries from OpenCode config files under each root.

        Checks two files per root:

        * ``<root>/.opencode/mcp.json`` — workspace-scoped (OpenCode native
          format: ``mcp`` key; ``command`` is a list).
        * ``<root>/.config/opencode/opencode.json`` — user-scoped (same format).

        The ``agent-skill-router`` entry is always excluded.
        """
        result: dict[str, NormalizedMcpServer] = {}
        for root in roots or [Path.cwd(), Path.home()]:
            for config_file in (
                root / ".opencode" / "mcp.json",
                root / ".config" / "opencode" / "opencode.json",
            ):
                if not config_file.exists():
                    continue
                try:
                    data: dict = json.loads(config_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                for name, entry in data.get("mcp", {}).items():
                    if name == _SELF_SERVER_NAME or name in result:
                        continue
                    normalized = _normalize_mcpserver_entry(entry)
                    if normalized is not None:
                        result[name] = normalized
        return result
