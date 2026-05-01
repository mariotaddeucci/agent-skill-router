"""Codex (OpenAI) MCP setup provider (paths only)."""

from pathlib import Path

from agent_skill_router.agents._base import AgentSetupProvider


class CodexSetupProvider(AgentSetupProvider):
    """Path provider for Codex (OpenAI CLI).

    Workspace: ``<cwd>/.codex/config.toml``
    User:      ``~/.codex/config.toml``

    Automated discovery and install are not implemented; edit
    ``~/.codex/config.toml`` manually following the Codex MCP documentation.
    """

    name = "codex"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".codex" / "config.toml"

    def config_path_user(self) -> Path:
        return Path.home() / ".codex" / "config.toml"
