from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from fastmcp.server.providers.skills import (
    ClaudeSkillsProvider,
    CodexSkillsProvider,
    CopilotSkillsProvider,
    CursorSkillsProvider,
    GeminiSkillsProvider,
    GooseSkillsProvider,
    OpenCodeSkillsProvider,
    SkillsDirectoryProvider,
    VSCodeSkillsProvider,
)

from agent_skill_router.settings import Settings

# Skills bundled inside this package — resolved relative to this file, works
# both in development (src layout) and after pip install.
_BUNDLED_SKILLS_PATH = Path(__file__).parent / "skills"

# Each entry: (settings_attr, provider_cls, roots_by_level)
# roots_by_level maps "workspace" | "user" -> list of paths for that level.
# Vendor classes are used for their own roots; SkillsDirectoryProvider is used
# when we need to pass a filtered subset of roots explicitly.
_PROVIDER_ROOTS: list[
    tuple[
        str,  # settings attribute name
        type,  # provider class
        dict[Literal["workspace", "user"], list[Path]],
    ]
] = [
    (
        "enable_claude",
        ClaudeSkillsProvider,
        {
            "workspace": [Path.cwd() / ".claude" / "skills"],
            "user": [Path.home() / ".claude" / "skills"],
        },
    ),
    (
        "enable_cursor",
        CursorSkillsProvider,
        {
            "workspace": [Path.cwd() / ".cursor" / "skills"],
            "user": [Path.home() / ".cursor" / "skills"],
        },
    ),
    (
        "enable_vscode",
        VSCodeSkillsProvider,
        {
            "workspace": [Path.cwd() / ".copilot" / "skills"],
            "user": [Path.home() / ".copilot" / "skills"],
        },
    ),
    (
        "enable_codex",
        CodexSkillsProvider,
        {
            "workspace": [Path.cwd() / ".codex" / "skills"],
            # /etc/codex/skills is system-managed, grouped under "user" scope
            "user": [Path("/etc/codex/skills"), Path.home() / ".codex" / "skills"],
        },
    ),
    (
        "enable_gemini",
        GeminiSkillsProvider,
        {
            "workspace": [Path.cwd() / ".gemini" / "skills"],
            "user": [Path.home() / ".gemini" / "skills"],
        },
    ),
    (
        "enable_goose",
        GooseSkillsProvider,
        {
            "workspace": [Path.cwd() / ".goose" / "skills"],
            "user": [Path.home() / ".config" / "agents" / "skills"],
        },
    ),
    (
        "enable_copilot",
        CopilotSkillsProvider,
        {
            "workspace": [Path.cwd() / ".copilot" / "skills"],
            "user": [Path.home() / ".copilot" / "skills"],
        },
    ),
    (
        "enable_opencode",
        OpenCodeSkillsProvider,
        {
            "workspace": [Path.cwd() / ".opencode" / "skills"],
            "user": [Path.home() / ".config" / "opencode" / "skills"],
        },
    ),
    (
        "enable_agents",
        SkillsDirectoryProvider,
        {
            "workspace": [Path.cwd() / ".agents" / "skills"],
            "user": [Path.home() / ".agents" / "skills"],
        },
    ),
    (
        "enable_openclaw",
        SkillsDirectoryProvider,
        {
            "workspace": [Path.cwd() / ".openclaw" / "skills"],
            "user": [Path.home() / ".openclaw" / "skills"],
        },
    ),
]


def _resolve_roots(
    roots_by_level: dict[Literal["workspace", "user"], list[Path]],
    enable_workspace: bool,
    enable_user: bool,
) -> list[Path]:
    """Return the subset of roots allowed by the scope flags that also exist on disk."""
    allowed: list[Path] = []
    if enable_workspace:
        allowed += roots_by_level.get("workspace", [])
    if enable_user:
        allowed += roots_by_level.get("user", [])
    return [r for r in allowed if r.exists()]


def build_mcp(settings: Settings | None = None) -> FastMCP:
    if settings is None:
        settings = Settings()

    mcp = FastMCP("Agent Skill Router")

    # --- Prompt: /create-skill ---
    @mcp.prompt(
        name="create-skill",
        description=(
            "Create or improve a skill. "
            "A skill is a reusable set of instructions that teaches an AI assistant how to perform "
            "a specific task. By default the skill is saved to the current workspace (.agents/skills/) "
            "so it is immediately available to all agents in this project. "
            "Set save_to_user_level=true to save it to ~/.agents/skills/ instead, making it "
            "available across all your workspaces."
        ),
    )
    def create_skill_prompt(
        goal: str,
        save_to_user_level: bool = False,
    ) -> str:
        """
        Args:
            goal: Describe the skill you want to create or improve.
            save_to_user_level: Save to ~/.agents/skills/ (all workspaces) instead of
                <cwd>/.agents/skills/ (this workspace only). Default: False.
        """
        if save_to_user_level:
            output_dir = Path.home() / ".agents" / "skills"
            scope_note = (
                f"Save the finished skill to `{output_dir}/<skill-name>/` so it is available across **all workspaces**."
            )
        else:
            output_dir = Path.cwd() / ".agents" / "skills"
            scope_note = (
                f"Save the finished skill to `{output_dir}/<skill-name>/` "
                f"so it is available to agents in **this workspace only**."
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        return (
            f"Use the **skill-creator** skill to help me with the following goal:\n\n"
            f"> {goal}\n\n"
            f"---\n\n"
            f"**What is a skill?** A skill is a directory containing a `SKILL.md` file with "
            f"structured instructions that an AI assistant can load to perform a specific task "
            f"consistently and well. Think of it as a reusable playbook for this project or for you personally.\n\n"
            f"**Output directory:** {scope_note}\n"
            f"The directory has already been created and is ready to use."
        )

    # supporting_files="resources" ensures every file in every skill is
    # individually listed, not hidden behind the manifest template.

    for attr, provider_cls, roots_by_level in _PROVIDER_ROOTS:
        if not getattr(settings, attr):
            continue

        roots = _resolve_roots(
            roots_by_level,
            enable_workspace=settings.enable_workspace_level,
            enable_user=settings.enable_user_level,
        )
        if not roots:
            continue

        # For vendor classes (single fixed root set), use the vendor class directly
        # only when all their roots survived the filter — otherwise fall back to
        # SkillsDirectoryProvider with just the allowed subset.
        all_roots = roots_by_level.get("workspace", []) + roots_by_level.get("user", [])
        if provider_cls is not SkillsDirectoryProvider and set(roots) == {r for r in all_roots if r.exists()}:
            mcp.add_provider(provider_cls(supporting_files="resources"))
        else:
            mcp.add_provider(SkillsDirectoryProvider(roots=roots, supporting_files="resources"))

    # --- Bundled skills (shipped with this package, not affected by scope flags) ---
    if settings.enable_bundled and _BUNDLED_SKILLS_PATH.exists():
        mcp.add_provider(SkillsDirectoryProvider(roots=[_BUNDLED_SKILLS_PATH], supporting_files="resources"))

    # --- Extra directories (always included, not affected by scope flags) ---
    for extra in settings.extra_dirs:
        if not extra.path.exists():
            continue
        mcp.add_provider(SkillsDirectoryProvider(roots=[extra.path], supporting_files="resources"))

    return mcp
