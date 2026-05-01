"""Cursor MCP setup provider."""

import json
from pathlib import Path

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, AgentSetupProvider, McpConfig


class CursorSetupProvider(AgentSetupProvider):
    """Setup provider for Cursor.

    Config file format: ``.cursor/mcp.json``

    Workspace scope: ``<cwd>/.cursor/mcp.json``
    User scope:      ``~/.cursor/mcp.json``

    Discovery: searches ``.cursor/mcp.json`` in the current working directory
    and ``~/.cursor/mcp.json`` for the user scope, returning whichever exist.

    Install: merges the MCP server entry under ``mcpServers.<name>`` using the
    Cursor MCP schema (``command``, ``args``). Existing entries are left
    untouched; the agent-skill-router entry is added or updated idempotently.
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
        The entry is written under ``mcpServers.agent-skill-router`` using the
        Cursor MCP schema::

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

        mcp_servers: dict = data.setdefault("mcpServers", {})
        mcp_servers["agent-skill-router"] = {
            "command": mcp_config.command,
            "args": mcp_config.args,
        }

        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
