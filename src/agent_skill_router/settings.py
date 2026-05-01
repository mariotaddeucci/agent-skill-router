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

    # Global scope filters — applied to all providers before checking existence.
    # extra_dirs are always included regardless of these flags (they are explicit).
    enable_workspace_level: bool = Field(default=True, description="Include workspace-scoped skill directories (<cwd>/...)")
    enable_user_level: bool = Field(default=True, description="Include user-scoped skill directories (~/.../skills/)")

    # Bundled skills shipped with the agent-skill-router package itself
    enable_bundled: bool = Field(default=True, description="Enable skills bundled inside the agent-skill-router package")

    # Individual vendor provider toggles (all enabled by default)
    # All vendors use the same SKILL.md format — only the directory differs.
    enable_claude: bool = Field(default=True, description="Enable ClaudeSkillsProvider (~/.claude/skills/)")
    enable_cursor: bool = Field(default=True, description="Enable CursorSkillsProvider (~/.cursor/skills/)")
    enable_vscode: bool = Field(default=True, description="Enable VSCodeSkillsProvider (~/.copilot/skills/)")
    enable_codex: bool = Field(default=True, description="Enable CodexSkillsProvider (/etc/codex/skills/ and ~/.codex/skills/)")
    enable_gemini: bool = Field(default=True, description="Enable GeminiSkillsProvider (~/.gemini/skills/)")
    enable_goose: bool = Field(default=True, description="Enable GooseSkillsProvider (~/.config/agents/skills/)")
    enable_copilot: bool = Field(default=True, description="Enable CopilotSkillsProvider (~/.copilot/skills/)")
    enable_opencode: bool = Field(default=True, description="Enable OpenCodeSkillsProvider (~/.config/opencode/skills/)")

    # Generic .agents/skills provider
    enable_agents: bool = Field(default=True, description="Enable generic agent skills (<cwd>/.agents/skills/ and ~/.agents/skills/)")

    # OpenClaw managed skills
    enable_openclaw: bool = Field(default=True, description="Enable OpenClaw managed skills (~/.openclaw/skills/)")

    # Extra directories to scan for skills (same SKILL.md format as all vendors)
    # Example: SKILL_ROUTER_EXTRA_DIRS='[{"path": "/some/path"}]'
    extra_dirs: list[ExtraDirectory] = Field(
        default_factory=list,
        description="Additional skill directories to expose. All use the standard SKILL.md format.",
    )
