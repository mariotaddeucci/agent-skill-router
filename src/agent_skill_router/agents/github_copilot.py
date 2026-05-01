"""GitHub Copilot (VS Code) MCP setup provider."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    AgentSetupProvider,
    McpConfig,
    PromptSlashCommand,
    SlashCommand,
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

    def list_prompts(self, root: Path | None = None) -> list[SlashCommand]:
        """Read prompts from ``.github/prompts/*.prompt.md`` under *root*.

        Each ``.prompt.md`` file may contain YAML frontmatter with a
        ``description`` key.  The command name is derived from the file stem
        with the trailing ``.prompt`` segment removed.

        Example file (``.github/prompts/fix-bug.prompt.md``)::

            ---
            mode: 'chat'
            description: 'Fix a bug in the selected code'
            ---
            You are an expert debugger...
        """
        prompts_dir = (root or Path.cwd()) / ".github" / "prompts"
        if not prompts_dir.is_dir():
            return []

        commands: list[SlashCommand] = []
        for path in sorted(prompts_dir.glob("*.prompt.md")):
            content = path.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(content)
            name = path.stem  # e.g. "fix-bug.prompt" → strip trailing ".prompt"
            if name.endswith(".prompt"):
                name = name[: -len(".prompt")]
            commands.append(
                PromptSlashCommand(
                    name=f"/{name}",
                    description=meta.get("description", ""),
                    prompt=body,
                )
            )
        return commands
