"""Goose MCP setup provider."""

from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, AgentSetupProvider, McpConfig


class GooseSetupProvider(AgentSetupProvider):
    """Setup provider for Goose (by Block).

    Config file format: YAML

    Workspace scope: ``<cwd>/.goose/mcp.json``
    User scope:      ``~/.config/goose/config.yaml``

    Discovery: returns whichever of the above paths exist on this machine.

    Install: merges the MCP server entry under ``extensions.agent-skill-router``
    using the Goose extension schema. Existing entries are left untouched; the
    agent-skill-router entry is added or updated idempotently.
    """

    name = "goose"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".goose" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".config" / "goose" / "config.yaml"

    def discover(self) -> list[Path]:
        """Return every Goose config file that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP extension entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``extensions.agent-skill-router`` using the
        Goose extension schema::

            extensions:
              agent-skill-router:
                args: [...]
                bundled: null
                cmd: uvx
                description: "Agent Skill Router MCP server"
                enabled: true
                envs: {}
                name: agent-skill-router
                timeout: 300
                type: stdio
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.preserve_quotes = True

        if config_path.exists():
            try:
                data = yaml.load(config_path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            if not isinstance(data, dict):
                data = {}
        else:
            data = {}

        extensions: dict = data.setdefault("extensions", {})
        extensions["agent-skill-router"] = {
            "args": list(mcp_config.args),
            "bundled": None,
            "cmd": mcp_config.command,
            "description": "Agent Skill Router MCP server",
            "enabled": True,
            "envs": {},
            "name": "agent-skill-router",
            "timeout": 300,
            "type": "stdio",
        }

        stream = StringIO()
        yaml.dump(data, stream)
        config_path.write_text(stream.getvalue(), encoding="utf-8")
