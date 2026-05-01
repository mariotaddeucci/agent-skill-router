"""Gemini CLI MCP setup provider (paths only)."""

from pathlib import Path

from agent_skill_router.agents._base import AgentSetupProvider


class GeminiSetupProvider(AgentSetupProvider):
    """Path provider for Gemini CLI.

    Workspace: ``<cwd>/.gemini/settings.json``
    User:      ``~/.gemini/settings.json``

    Automated discovery and install are not implemented; edit the config
    file manually following the Gemini CLI MCP documentation.
    """

    name = "gemini"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".gemini" / "settings.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".gemini" / "settings.json"
