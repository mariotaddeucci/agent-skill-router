"""Claude Code / Claude Desktop MCP setup provider."""

import json
from pathlib import Path

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, AgentSetupProvider, McpConfig


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
    """

    name = "claude"

    def config_path_workspace(self) -> Path:
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
