"""Abstract base class for agent MCP setup providers."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class NormalizedMcpServer:
    """A normalized MCP server entry read from an agent config file."""

    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None


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

#: Name of the agent-skill-router MCP server entry — excluded from proxy reads.
_SELF_SERVER_NAME = "agent-skill-router"


def _normalize_mcpserver_entry(entry: dict) -> NormalizedMcpServer | None:
    """Convert an agent-specific MCP server dict to :class:`NormalizedMcpServer`.

    Handles two shapes:

    * Standard JSON (Claude, Cursor, GitHub Copilot, Gemini, Goose):
      ``{"command": "uvx", "args": [...], "env": {...}}``
    * OpenCode list-command JSON:
      ``{"type": "local", "command": ["uvx", ...], "enabled": true}``
    * Remote HTTP/SSE:
      ``{"url": "https://..."}``
    """
    if not isinstance(entry, dict):
        return None

    url = entry.get("url")
    if url:
        env = {str(k): str(v) for k, v in entry.get("env", {}).items()}
        return NormalizedMcpServer(url=str(url), env=env)

    raw_command = entry.get("command")
    if raw_command is None:
        return None

    if isinstance(raw_command, list):
        # OpenCode uses command as a list: [executable, arg1, arg2, ...]
        if not raw_command:
            return None
        cmd: str = str(raw_command[0])
        args: list[str] = [str(a) for a in raw_command[1:]]
    else:
        cmd = str(raw_command)
        args = [str(a) for a in entry.get("args", [])]

    env = {str(k): str(v) for k, v in entry.get("env", {}).items()}
    return NormalizedMcpServer(command=cmd, args=args, env=env)


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
    def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]:
        """Read existing slash commands from the agent's native prompt files.

        Scans agent-specific prompt directories under each path in *roots*
        (defaults to ``[Path.cwd()]``) and returns parsed :class:`SlashCommand`
        objects. First-wins deduplication applies when the same command name
        appears in multiple roots.
        """

    def read_mcp_servers(self, roots: list[Path] | None = None) -> dict[str, NormalizedMcpServer]:
        """Read MCP server entries from this agent's config files.

        Scans agent-specific config files under each path in *roots* and returns
        a dict mapping server name to :class:`NormalizedMcpServer`. The entry
        named ``agent-skill-router`` is always excluded to avoid self-proxying.
        First-wins deduplication applies across multiple roots.

        Returns an empty dict by default; providers that support reading MCP
        server entries should override this method.
        """
        return {}
