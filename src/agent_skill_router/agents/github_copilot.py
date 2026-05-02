"""GitHub Copilot (VS Code) MCP setup provider."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    _SELF_SERVER_NAME,
    AgentSetupProvider,
    McpConfig,
    NormalizedMcpServer,
    PromptSlashCommand,
    SlashCommand,
    _normalize_mcpserver_entry,
    _parse_frontmatter,
)

if TYPE_CHECKING:
    from agent_skill_router._skills import SkillEntry


class GitHubCopilotSetupProvider(AgentSetupProvider):
    """Setup provider for GitHub Copilot (VS Code).

    Config file format: ``.vscode/mcp.json``

    Workspace scope: ``<cwd>/.vscode/mcp.json``
    User scope:      ``~/.vscode/mcp.json``

    Discovery: searches ``.vscode/mcp.json`` in the current working directory
    and ``~/.vscode/mcp.json`` for the user scope, returning whichever exist.

    Install: merges the MCP server entry under ``servers.<name>`` using a
    VS Code-compatible schema (``type``, ``command``, ``args``). Existing
    entries are left untouched; the agent-skill-router entry is added or
    updated idempotently.
    """

    name = "github-copilot"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".vscode" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".vscode" / "mcp.json"

    def discover(self) -> list[Path]:
        """Return every ``mcp.json`` that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.
        The entry is written under ``servers.agent-skill-router`` using the
        VS Code MCP schema::

            {
              "servers": {
                "agent-skill-router": {
                  "type": "stdio",
                  "command": "...",
                  "args": [...]
                }
              }
            }
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.exists():
            try:
                data: dict = json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}

        servers: dict = data.setdefault("servers", {})
        servers["agent-skill-router"] = {
            "type": "stdio",
            "command": mcp_config.command,
            "args": mcp_config.args,
        }

        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get_slash_commands(self, skills: list["SkillEntry"]) -> list[SlashCommand]:
        """Convert skills into GitHub Copilot slash commands (prompts)."""
        commands: list[SlashCommand] = []
        for skill in skills:
            skill_md = skill.directory / "SKILL.md"
            if not skill_md.exists():
                continue

            commands.append(
                PromptSlashCommand(
                    name=f"/{skill.name}",
                    description=skill.description,
                    prompt=skill_md.read_text(encoding="utf-8"),
                )
            )
        return commands

    def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]:
        """Discover GitHub Copilot prompt files and return them as slash commands.

        Scans ``.github/prompts/*.prompt.md`` under each root directory. Each
        file's YAML front-matter ``description`` field is used as the command
        description; the body (after the front-matter block) becomes the prompt
        text. Duplicate stems are silently skipped — the first occurrence wins.

        Parameters:
          - roots: list[Path] | None - Base directories to search. Defaults to
            ``[Path.cwd()]`` when *None*.

        Returns:
          list[SlashCommand] - One ``PromptSlashCommand`` per unique
          ``*.prompt.md`` file discovered, ordered by filename within each root.
        """
        seen: set[str] = set()
        commands: list[SlashCommand] = []
        for root in roots or [Path.cwd()]:
            prompts_dir = root / ".github" / "prompts"
            if not prompts_dir.is_dir():
                continue
            for path in sorted(prompts_dir.glob("*.prompt.md")):
                name = path.stem
                if name.endswith(".prompt"):
                    name = name[: -len(".prompt")]
                if name in seen:
                    continue
                seen.add(name)
                content = path.read_text(encoding="utf-8")
                meta, body = _parse_frontmatter(content)
                commands.append(
                    PromptSlashCommand(
                        name=f"/{name}",
                        description=meta.get("description", ""),
                        prompt=body,
                    )
                )
        return commands

    def read_mcp_servers(self, roots: list[Path] | None = None) -> dict[str, NormalizedMcpServer]:
        """Read MCP server entries from ``.vscode/mcp.json`` under each root.

        Parses the ``servers`` key of GitHub Copilot's VS Code JSON config. The
        ``agent-skill-router`` entry is always excluded.
        """
        result: dict[str, NormalizedMcpServer] = {}
        for root in roots or [Path.cwd(), Path.home()]:
            config_file = root / ".vscode" / "mcp.json"
            if not config_file.exists():
                continue
            try:
                data: dict = json.loads(config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for name, entry in data.get("servers", {}).items():
                if name == _SELF_SERVER_NAME or name in result:
                    continue
                normalized = _normalize_mcpserver_entry(entry)
                if normalized is not None:
                    result[name] = normalized
        return result
