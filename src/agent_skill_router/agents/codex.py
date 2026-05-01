"""Codex (OpenAI) MCP setup provider."""

import tomllib
from pathlib import Path

import tomli_w

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, AgentSetupProvider, McpConfig


class CodexSetupProvider(AgentSetupProvider):
    """Setup provider for Codex (OpenAI CLI).

    Config file format: TOML

    Workspace: ``<cwd>/.codex/config.toml``
    User:      ``~/.codex/config.toml``

    Discovery: searches both paths and returns whichever exist.

    Install: merges the MCP server entry under ``mcp_servers.agent-skill-router``
    using the Codex TOML schema (``command``, ``args``). Existing entries are
    left untouched; the agent-skill-router entry is added or updated idempotently.
    """

    name = "codex"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".codex" / "config.toml"

    def config_path_user(self) -> Path:
        return Path.home() / ".codex" / "config.toml"

    def discover(self) -> list[Path]:
        """Return every ``config.toml`` that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``mcp_servers.agent-skill-router`` using the
        Codex TOML schema::

            [mcp_servers.agent-skill-router]
            command = "uvx"
            args = ["--from", "...", "agent-skill-router", "run"]
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.exists():
            try:
                data: dict = tomllib.loads(config_path.read_text(encoding="utf-8"))
            except (tomllib.TOMLDecodeError, OSError):
                data = {}
        else:
            data = {}

        mcp_servers: dict = data.setdefault("mcp_servers", {})
        mcp_servers["agent-skill-router"] = {
            "command": mcp_config.command,
            "args": mcp_config.args,
        }

        config_path.write_text(tomli_w.dumps(data), encoding="utf-8")
