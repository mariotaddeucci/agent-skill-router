"""Claude Code / Claude Desktop MCP setup provider."""

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


class ClaudeSetupProvider(AgentSetupProvider):
    """Setup provider for Claude (Claude Code / Claude Desktop).

    Config file format: ``.claude/mcp.json``

    Workspace scope: ``<cwd>/.claude/mcp.json``
    User scope:      ``~/.claude/mcp.json``

    Discovery: searches ``.claude/mcp.json`` in the current working directory
    and ``~/.claude/mcp.json`` for the user scope, returning whichever exist.

    Install: merges the MCP server entry under ``mcpServers.<name>`` using the
    Claude Code JSON schema (``type``, ``command``, ``args``). Existing entries
    are left untouched; the agent-skill-router entry is added or updated
    idempotently.

    Prompts: reads custom slash commands from ``.claude/commands/*.md`` files.
    """

    name = "claude"

    def config_path_workspace(self) -> Path:
        """Return the workspace-scoped Claude MCP config path.

        Returns:
            Path — ``<cwd>/.claude/mcp.json``
        """
        return Path.cwd() / ".claude" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".claude" / "mcp.json"

    def discover(self) -> list[Path]:
        """Return every ``mcp.json`` that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``mcpServers.agent-skill-router`` using the
        Claude Code MCP schema::

            {
              "mcpServers": {
                "agent-skill-router": {
                  "type": "stdio",
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
            "type": "stdio",
            "command": mcp_config.command,
            "args": mcp_config.args,
        }

        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get_slash_commands(self, skills: list["SkillEntry"]) -> list[SlashCommand]:
        """Convert skills into Claude Code slash commands (prompts)."""
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
        """Discover Claude Code slash commands from ``.claude/commands/*.md`` files.

        Scans each root directory for Markdown files under ``.claude/commands/``.
        Files are sorted alphabetically; the first file found for a given stem
        (command name) wins — duplicates across roots are skipped.

        Parameters:
            roots: Directories to search. Defaults to ``[Path.cwd()]`` when
                ``None``.

        Returns:
            list[SlashCommand] — one ``PromptSlashCommand`` per discovered
            ``.md`` file, with ``name`` set to ``/<stem>`` and ``description``
            read from the file's YAML front-matter ``description`` field (empty
            string if absent).
        """
        seen: set[str] = set()
        commands: list[SlashCommand] = []
        for root in roots or [Path.cwd()]:
            commands_dir = root / ".claude" / "commands"
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
        """Read MCP server entries from ``.claude/mcp.json`` under each root.

        Parses the ``mcpServers`` key of Claude's JSON config. The
        ``agent-skill-router`` entry is always excluded.
        """
        result: dict[str, NormalizedMcpServer] = {}
        for root in roots or [Path.cwd(), Path.home()]:
            config_file = root / ".claude" / "mcp.json"
            if not config_file.exists():
                continue
            try:
                data: dict = json.loads(config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for name, entry in data.get("mcpServers", {}).items():
                if name == _SELF_SERVER_NAME or name in result:
                    continue
                normalized = _normalize_mcpserver_entry(entry)
                if normalized is not None:
                    result[name] = normalized
        return result
