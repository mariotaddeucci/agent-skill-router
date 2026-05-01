"""Claude Code / Claude Desktop MCP setup provider (paths only)."""

from pathlib import Path

from agent_skill_router.agents._base import AgentSetupProvider


class ClaudeSetupProvider(AgentSetupProvider):
    """Path provider for Claude (Claude Code / Claude Desktop).

    Workspace: ``<cwd>/.claude/mcp.json``
    User:      ``~/.claude/mcp.json``

    Automated discovery and install are not implemented; use the Claude Code
    CLI (``claude mcp add``) or edit the config manually.
    """

    name = "claude"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".claude" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".claude" / "mcp.json"
