"""Gemini CLI MCP setup provider."""

import json
from pathlib import Path

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, AgentSetupProvider, McpConfig


class GeminiSetupProvider(AgentSetupProvider):
    """Setup provider for Gemini CLI.

    Config file format: ``.gemini/settings.json``

    Workspace scope: ``<cwd>/.gemini/settings.json``
    User scope:      ``~/.gemini/settings.json``

    Discovery: searches ``.gemini/settings.json`` in the current working
    directory and ``~/.gemini/settings.json`` for the user scope, returning
    whichever exist.

    Install: merges the MCP server entry under ``mcpServers.agent-skill-router``
    using the Gemini CLI JSON schema (``command``, ``args``). Existing entries
    are left untouched; the agent-skill-router entry is added or updated
    idempotently.
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
        The entry is written under ``mcpServers.agent-skill-router`` using the
        Gemini CLI MCP schema::

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
