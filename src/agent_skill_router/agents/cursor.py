"""Cursor MCP setup provider (paths only)."""

from pathlib import Path

from agent_skill_router.agents._base import AgentSetupProvider


class CursorSetupProvider(AgentSetupProvider):
    """Path provider for Cursor.

    Workspace: ``<cwd>/.cursor/mcp.json``
    User:      ``~/.cursor/mcp.json``

    Automated discovery and install are not implemented; edit the config
    file manually following the Cursor MCP documentation.
    """

    name = "cursor"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".cursor" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".cursor" / "mcp.json"
