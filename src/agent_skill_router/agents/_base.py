"""Abstract base class for agent MCP setup providers."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agent_skill_router._skills import SkillEntry


@dataclass(frozen=True)
class McpConfig:
    """Minimal representation of the MCP server entry to inject."""

    command: str
    args: list[str]


class BaseSlashCommand(BaseModel):
    """Base representation of a slash command."""

    name: str
    description: str


class PromptSlashCommand(BaseSlashCommand):
    """Slash command that expands into a prompt."""

    type: Literal["prompt"] = "prompt"
    prompt: str


class ToolSlashCommand(BaseSlashCommand):
    """Slash command that triggers a tool."""

    type: Literal["tool"] = "tool"
    tool: str


class ResourceSlashCommand(BaseSlashCommand):
    """Slash command that opens a resource."""

    type: Literal["resource"] = "resource"
    uri: str


SlashCommand = Annotated[
    PromptSlashCommand | ToolSlashCommand | ResourceSlashCommand,
    Field(discriminator="type"),
]

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_FRONTMATTER_KV_RE = re.compile(r"^(\w[\w-]*)\s*:\s*(.*)$")


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse YAML-style frontmatter from markdown content.

    Returns ``(meta, body)`` where *meta* is a flat ``str → str`` dict
    (values are stripped of surrounding quotes) and *body* is the content
    after the closing ``---``. When no frontmatter is present both values
    are empty / the full content.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        kv = _FRONTMATTER_KV_RE.match(line)
        if kv:
            meta[kv.group(1)] = kv.group(2).strip().strip("'\"")

    return meta, content[match.end() :]


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

    @abstractmethod
    def discover(self) -> list[Path]:
        """Return existing config file paths detected on this machine.

        Returns an empty list when the agent is not installed / not configured.
        """

    @abstractmethod
    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Inject *mcp_config* into the agent's config file at *config_path*.

        Creates the config file (and parent directories) if it does not exist.
        Must be idempotent — calling twice with the same config is safe.
        """

    @abstractmethod
    def get_slash_commands(self, skills: list["SkillEntry"]) -> list[SlashCommand]:
        """Convert a list of skills into agent-specific slash commands."""

    @abstractmethod
    def list_prompts(self, root: Path | None = None) -> list[SlashCommand]:
        """Read existing slash commands from the agent's native prompt files.

        Scans agent-specific prompt directories under *root* (defaults to
        ``Path.cwd()``) and returns parsed :class:`SlashCommand` objects.
        """
