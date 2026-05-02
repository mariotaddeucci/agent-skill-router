"""Goose MCP setup provider."""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from agent_skill_router.agents._base import (
    _DEFAULT_MCP_CONFIG,
    AgentSetupProvider,
    McpConfig,
    PromptSlashCommand,
    SlashCommand,
)

if TYPE_CHECKING:
    from agent_skill_router._skills import SkillEntry


def _parse_goose_recipe(content: str) -> dict:
    """Parse a Goose recipe YAML file and return its fields as a dict."""
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    return {}


_GOOSE_ENTRY_RE = re.compile(
    r"^( {2})agent-skill-router:\n(?:\1  [^\n]*\n)*",
    re.MULTILINE,
)


def _goose_yaml_entry(mcp_config: McpConfig) -> str:
    """Return the YAML snippet for the agent-skill-router extension block."""
    args_lines = "".join(f"      - {a}\n" for a in mcp_config.args)
    return (
        f"  agent-skill-router:\n"
        f"    args:\n"
        f"{args_lines}"
        f"    cmd: {mcp_config.command}\n"
        f"    enabled: true\n"
        f"    name: agent-skill-router\n"
        f"    type: stdio\n"
    )


def _merge_yaml_extensions(content: str, mcp_config: McpConfig) -> str:
    """Merge or insert the agent-skill-router entry into Goose ``config.yaml``.

    Replaces an existing ``agent-skill-router`` block under ``extensions:`` or
    appends a fresh ``extensions:`` section when it is absent.
    """
    entry = _goose_yaml_entry(mcp_config)

    if _GOOSE_ENTRY_RE.search(content):
        return _GOOSE_ENTRY_RE.sub(entry, content)

    if re.search(r"^extensions:", content, re.MULTILINE):
        return re.sub(r"(^extensions:\n)", rf"\1{entry}", content, count=1, flags=re.MULTILINE)

    separator = "\n" if content and not content.endswith("\n") else ""
    return content + separator + "extensions:\n" + entry


class GooseSetupProvider(AgentSetupProvider):
    """Setup provider for Goose.

    Workspace: ``<cwd>/.goose/mcp.json``  (JSON)
    User:      ``~/.config/goose/config.yaml``  (YAML)

    Discovery: searches both paths and returns whichever exist.

    Install:
    - Workspace JSON — merges under ``mcpServers.agent-skill-router``.
    - User YAML — merges or inserts the extension block under ``extensions:``.

    Prompts: reads custom prompts from ``.goose/prompts/*.md`` files.
    """

    name = "goose"

    def config_path_workspace(self) -> Path:
        return Path.cwd() / ".goose" / "mcp.json"

    def config_path_user(self) -> Path:
        return Path.home() / ".config" / "goose" / "config.yaml"

    def discover(self) -> list[Path]:
        """Return every config path that already exists on this machine."""
        candidates = [self.config_path_workspace(), self.config_path_user()]
        return [p for p in candidates if p.exists()]

    def install(self, config_path: Path, mcp_config: McpConfig = _DEFAULT_MCP_CONFIG) -> None:
        """Merge the MCP server entry into *config_path*.

        Creates the file (and parent dirs) when it does not exist.

        For ``.json`` paths (workspace), writes under ``mcpServers``::

            {
              "mcpServers": {
                "agent-skill-router": {
                  "type": "stdio",
                  "command": "...",
                  "args": [...]
                }
              }
            }

        For ``.yaml`` / ``.yml`` paths (user), writes under ``extensions``::

            extensions:
              agent-skill-router:
                args: [...]
                cmd: uvx
                enabled: true
                name: agent-skill-router
                type: stdio
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.suffix in (".yaml", ".yml"):
            content = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
            config_path.write_text(_merge_yaml_extensions(content, mcp_config), encoding="utf-8")
        else:
            if config_path.exists():
                try:
                    data: dict = json.loads(config_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    data = {}
            else:
                data = {}

            servers: dict = data.setdefault("mcpServers", {})
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
        """Convert skills into Goose slash commands (prompts)."""
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
        """Read recipes from ``.goose/recipes/*.yaml`` under each root."""
        seen: set[str] = set()
        commands: list[SlashCommand] = []
        for root in roots or [Path.cwd()]:
            recipes_dir = root / ".goose" / "recipes"
            if not recipes_dir.is_dir():
                continue
            for path in sorted(recipes_dir.glob("*.yaml")):
                try:
                    data = _parse_goose_recipe(path.read_text(encoding="utf-8"))
                except OSError:
                    continue

                title = str(data.get("title", path.stem))
                if title in seen:
                    continue
                seen.add(title)
                prompt_body = str(data.get("instructions") or data.get("prompt", ""))
                commands.append(
                    PromptSlashCommand(
                        name=f"/{title}",
                        description=str(data.get("description", "")),
                        prompt=prompt_body,
                    )
                )
        return commands
