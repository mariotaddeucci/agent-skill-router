"""Agent MCP setup providers."""

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    _SELF_SERVER_NAME,
    AgentSetupProvider,
    McpConfig,
    NormalizedMcpServer,
    _normalize_mcpserver_entry,
)
from agent_skill_router.agents.claude import ClaudeSetupProvider
from agent_skill_router.agents.codex import CodexSetupProvider
from agent_skill_router.agents.cursor import CursorSetupProvider
from agent_skill_router.agents.gemini import GeminiSetupProvider
from agent_skill_router.agents.github_copilot import GitHubCopilotSetupProvider
from agent_skill_router.agents.goose import GooseSetupProvider
from agent_skill_router.agents.opencode import OpenCodeSetupProvider

#: All registered providers, keyed by their ``name`` attribute.
AGENT_PROVIDERS: dict[str, AgentSetupProvider] = {
    p.name: p
    for p in [
        GitHubCopilotSetupProvider(),
        ClaudeSetupProvider(),
        CursorSetupProvider(),
        OpenCodeSetupProvider(),
        GooseSetupProvider(),
        GeminiSetupProvider(),
        CodexSetupProvider(),
    ]
}

__all__ = [
    "AGENT_PROVIDERS",
    "_DEFAULT_MCP_CONFIG",
    "_SELF_SERVER_NAME",
    "AgentSetupProvider",
    "ClaudeSetupProvider",
    "CodexSetupProvider",
    "CursorSetupProvider",
    "GeminiSetupProvider",
    "GitHubCopilotSetupProvider",
    "GooseSetupProvider",
    "McpConfig",
    "NormalizedMcpServer",
    "OpenCodeSetupProvider",
    "_normalize_mcpserver_entry",
]
