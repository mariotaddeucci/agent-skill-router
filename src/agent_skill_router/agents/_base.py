"""Abstract base class for agent MCP setup providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class McpConfig:
    """Minimal representation of the MCP server entry to inject."""

    command: str
    args: list[str]


# Default MCP server config for agent-skill-router
_DEFAULT_MCP_CONFIG = McpConfig(
    command="uvx",
    args=[
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router",
        "run",
    ],
)


class AgentSetupProvider(ABC):
    """Base class for all agent MCP setup providers.

    Subclasses must implement:
    - ``config_path_workspace`` / ``config_path_user``: return the path to the
      agent's config file for each scope.
    - ``discover``: detect whether the agent is installed on this machine.
    - ``install``: write the MCP server entry into the agent's config file.

    ``discover`` and ``install`` have default implementations only in
    ``GitHubCopilotSetupProvider``; all other providers raise
    ``NotImplementedError`` for those two methods.
    """

    #: Short identifier used as ``--agent`` CLI argument (e.g. ``"github-copilot"``)
    name: str

    @abstractmethod
    def config_path_workspace(self) -> Path:
        """Return the path to the workspace-scoped config file."""

    @abstractmethod
    def config_path_user(self) -> Path:
        """Return the path to the user-scoped (global) config file."""

    def config_path(self, *, user: bool) -> Path:
        """Return the appropriate config path based on *user* flag."""
        return self.config_path_user() if user else self.config_path_workspace()

    def discover(self) -> list[Path]:
        """Return existing config file paths detected on this machine.

        Returns an empty list when the agent is not installed / not configured.
        Default implementation: not supported — subclasses that support
        auto-discovery override this.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support auto-discovery")

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Inject *mcp_config* into the agent's config file at *config_path*.

        Creates the config file (and parent directories) if it does not exist.
        Must be idempotent — calling twice with the same config is safe.
        Default implementation: not supported — subclasses override this.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support automated install")
