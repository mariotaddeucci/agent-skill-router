"""OpenCode MCP setup provider (paths only)."""

from pathlib import Path

from agent_skill_router.agents._base import AgentSetupProvider


class OpenCodeSetupProvider(AgentSetupProvider):
    """Path provider for OpenCode.

    Workspace: ``<cwd>/.opencode/mcp.json``
    User:      ``~/.config/opencode/opencode.json``

    Automated discovery and install are not implemented; edit
    ``~/.config/opencode/opencode.json`` manually following the OpenCode
    MCP documentation.
    """

    name = "opencode"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".opencode" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".config" / "opencode" / "opencode.json"
