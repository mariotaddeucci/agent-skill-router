"""Goose MCP setup provider (paths only)."""

from pathlib import Path

from agent_skill_router.agents._base import AgentSetupProvider


class GooseSetupProvider(AgentSetupProvider):
    """Path provider for Goose.

    Workspace: ``<cwd>/.goose/mcp.json``
    User:      ``~/.config/goose/config.yaml``

    Automated discovery and install are not implemented; configure Goose
    via Advanced settings → Extensions or edit the config file directly.
    """

    name = "goose"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".goose" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".config" / "goose" / "config.yaml"
