from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtraDirectory(BaseSettings):
    """Configuration for an extra skills directory to scan."""

    path: Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SKILL_ROUTER_",
        env_nested_delimiter="__",
    )

    # Explicit workspace root — when set, skips git-root detection and uses
    # this directory directly. Overridden by the --workspace-dir CLI flag.
    workspace_dir: Path | None = Field(
        default=None,
        description=(
            "Explicit workspace root directory. Overrides git-root auto-detection. "
            "When unset, the git repository root (or cwd) is used."
        ),
    )

    # Global scope filters — applied to all providers before checking existence.
    # extra_dirs are always included regardless of these flags (they are explicit).
    enable_workspace_level: bool = Field(
        default=True,
        description="Include workspace-scoped skill directories (<cwd>/...)",
    )
    enable_user_level: bool = Field(
        default=True,
        description="Include user-scoped skill directories (~/.../skills/)",
    )

    # Bundled skills shipped with the agent-skill-router package itself
    enable_bundled: bool = Field(
        default=True,
        description="Enable skills bundled inside the agent-skill-router package",
    )

    # Default state for all vendor providers.
    # Set to False to disable every provider, then opt-in individually via
    # their specific enable_<name> flag.
    providers_default: bool = Field(
        default=True,
        description=(
            "Default enabled state applied to every vendor provider whose specific "
            "enable_<name> flag is not explicitly set. "
            "Set to False to disable all providers and opt-in one by one."
        ),
    )

    # Individual vendor provider overrides — None means 'use providers_default'.
    # All vendors use the same SKILL.md format — only the directory differs.
    enable_claude: bool | None = Field(default=None, description="Enable ClaudeSkillsProvider (~/.claude/skills/)")
    enable_cursor: bool | None = Field(default=None, description="Enable CursorSkillsProvider (~/.cursor/skills/)")
    enable_vscode: bool | None = Field(default=None, description="Enable VSCodeSkillsProvider (~/.copilot/skills/)")
    enable_codex: bool | None = Field(
        default=None,
        description="Enable CodexSkillsProvider (/etc/codex/skills/ and ~/.codex/skills/)",
    )
    enable_gemini: bool | None = Field(default=None, description="Enable GeminiSkillsProvider (~/.gemini/skills/)")
    enable_goose: bool | None = Field(default=None, description="Enable GooseSkillsProvider (~/.config/agents/skills/)")
    enable_copilot: bool | None = Field(default=None, description="Enable CopilotSkillsProvider (~/.copilot/skills/)")
    enable_opencode: bool | None = Field(
        default=None,
        description="Enable OpenCodeSkillsProvider (~/.config/opencode/skills/)",
    )

    # Generic .agents/skills provider
    enable_agents: bool | None = Field(
        default=None,
        description="Enable generic agent skills (<cwd>/.agents/skills/ and ~/.agents/skills/)",
    )

    # OpenClaw managed skills
    enable_openclaw: bool | None = Field(
        default=None, description="Enable OpenClaw managed skills (~/.openclaw/skills/)"
    )

    def is_provider_enabled(self, attr: str) -> bool:
        """Return the effective enabled state for a vendor provider attribute.

        Resolves None (unset) to providers_default, allowing a single flag to
        disable all providers at once while still allowing per-provider opt-in.
        """
        value: bool | None = getattr(self, attr)
        return value if value is not None else self.providers_default

    # Extra directories to scan for skills (same SKILL.md format as all vendors)
    extra_dirs: list[ExtraDirectory] = Field(
        default_factory=list,
        description="Additional skill directories to expose. All use the standard SKILL.md format.",
    )
