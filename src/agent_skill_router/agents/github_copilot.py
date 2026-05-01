"""GitHub Copilot (VS Code) MCP setup provider."""

import json
from pathlib import Path

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, AgentSetupProvider, McpConfig


class GitHubCopilotSetupProvider(AgentSetupProvider):
    """Setup provider for GitHub Copilot (VS Code).

    Config file format: ``.vscode/mcp.json``

    Workspace scope: ``<cwd>/.vscode/mcp.json``
    User scope:      ``~/.vscode/mcp.json``

    Discovery: searches ``.vscode/mcp.json`` in the current working directory
    and ``~/.vscode/mcp.json`` for the user scope, returning whichever exist.

    Install: merges the MCP server entry under ``servers.<name>`` using a
    VS Code-compatible schema (``type``, ``command``, ``args``). Existing
    entries are left untouched; the agent-skill-router entry is added or
    updated idempotently.
    """

    name = "github-copilot"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".vscode" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".vscode" / "mcp.json"

    def discover(self) -> list[Path]:
        """Return every ``mcp.json`` that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``servers.agent-skill-router`` using the
        VS Code MCP schema::

            {
              "servers": {
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

        servers: dict = data.setdefault("servers", {})
        servers["agent-skill-router"] = {
            "type": "stdio",
            "command": mcp_config.command,
            "args": mcp_config.args,
        }

        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
