from collections.abc import Callable
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError
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

from agent_skill_router.agents import AGENT_PROVIDERS
from agent_skill_router.agents._base import PromptSlashCommand
from agent_skill_router.settings import Settings

# Skills bundled inside this package — resolved relative to this file, works
# both in development (src layout) and after pip install.
_BUNDLED_SKILLS_PATH = Path(__file__).parent / "skills"

# Template for provider roots — workspace paths use a "{workspace}" placeholder
# replaced at runtime by the resolved workspace root (git root or cwd).
# Each entry: (settings_attr, provider_cls, roots_by_level_template)
_PROVIDER_ROOTS: list[
    tuple[
        str,  # settings attribute name
        type,  # provider class
        dict[Literal["workspace", "user"], list[str | Path]],
    ]
] = [
    (
        "enable_claude",
        ClaudeSkillsProvider,
        {
            "workspace": ["{workspace}/.claude/skills"],
            "user": [Path.home() / ".claude" / "skills"],
        },
    ),
    (
        "enable_cursor",
        CursorSkillsProvider,
        {
            "workspace": ["{workspace}/.cursor/skills"],
            "user": [Path.home() / ".cursor" / "skills"],
        },
    ),
    (
        "enable_vscode",
        VSCodeSkillsProvider,
        {
            "workspace": ["{workspace}/.github/skills"],
            "user": [Path.home() / ".copilot" / "skills"],
        },
    ),
    (
        "enable_codex",
        CodexSkillsProvider,
        {
            "workspace": ["{workspace}/.codex/skills"],
            # /etc/codex/skills is system-managed, grouped under "user" scope
            "user": [Path("/etc/codex/skills"), Path.home() / ".codex" / "skills"],
        },
    ),
    (
        "enable_gemini",
        GeminiSkillsProvider,
        {
            "workspace": ["{workspace}/.gemini/skills"],
            "user": [Path.home() / ".gemini" / "skills"],
        },
    ),
    (
        "enable_goose",
        GooseSkillsProvider,
        {
            "workspace": ["{workspace}/.goose/skills"],
            "user": [Path.home() / ".config" / "agents" / "skills"],
        },
    ),
    (
        "enable_github_copilot",
        CopilotSkillsProvider,
        {
            "workspace": ["{workspace}/.github/skills"],
            "user": [Path.home() / ".copilot" / "skills"],
        },
    ),
    (
        "enable_opencode",
        OpenCodeSkillsProvider,
        {
            "workspace": ["{workspace}/.opencode/skills"],
            "user": [Path.home() / ".config" / "opencode" / "skills"],
        },
    ),
    (
        "enable_agents",
        SkillsDirectoryProvider,
        {
            "workspace": ["{workspace}/.agents/skills"],
            "user": [Path.home() / ".agents" / "skills"],
        },
    ),
    (
        "enable_openclaw",
        SkillsDirectoryProvider,
        {
            "workspace": ["{workspace}/.openclaw/skills"],
            "user": [Path.home() / ".openclaw" / "skills"],
        },
    ),
]


def _git_root(start: Path) -> Path:
    """Walk up from *start* looking for a ``.git`` directory or file.

    Returns the directory that contains ``.git`` when found, otherwise
    returns *start* unchanged.
    """
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start.resolve()


def workspace_root(directory: Path | None = None) -> Path:
    """Return the effective workspace root.

    Resolution order:
    1. *directory* — if explicitly provided, use it as-is (no git detection).
    2. Git root — if ``Path.cwd()`` (or *directory*) is inside a git repo,
       walk up to find the repository root.
    3. ``Path.cwd()`` — fallback when no git repo is found.
    """
    if directory is not None:
        return directory.resolve()
    return _git_root(Path.cwd())


def _expand_workspace(
    roots_by_level_template: dict[Literal["workspace", "user"], list[str | Path]],
    workspace: Path,
) -> dict[Literal["workspace", "user"], list[Path]]:
    """Resolve ``{workspace}`` placeholders in workspace path templates."""
    result: dict[Literal["workspace", "user"], list[Path]] = {}
    for level, paths in roots_by_level_template.items():
        result[level] = [
            Path(str(p).replace("{workspace}", str(workspace))) if isinstance(p, str) else p for p in paths
        ]
    return result


def _static_prompt(body: str) -> Callable[[], str]:
    """Return a no-argument function that yields *body* as an MCP prompt."""

    def _fn() -> str:
        return body

    return _fn


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


def build_mcp(settings: Settings | None = None, workspace_dir: Path | None = None) -> FastMCP:
    if settings is None:
        settings = Settings()

    # Explicit workspace_dir argument takes priority over settings.workspace_dir,
    # which in turn takes priority over git-root / cwd auto-detection.
    ws = workspace_root(workspace_dir if workspace_dir is not None else settings.workspace_dir)

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
                <workspace>/.agents/skills/ (this workspace only). Default: False.
        """
        if save_to_user_level:
            output_dir = Path.home() / ".agents" / "skills"
            scope_note = (
                f"Save the finished skill to `{output_dir}/<skill-name>/` so it is available across **all workspaces**."
            )
        else:
            output_dir = ws / ".agents" / "skills"
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

    for attr, _provider_cls, roots_by_level_template in _PROVIDER_ROOTS:
        if not settings.is_provider_enabled(attr):
            continue

        roots_by_level = _expand_workspace(roots_by_level_template, ws)
        roots = _resolve_roots(
            roots_by_level,
            enable_workspace=settings.enable_workspace_level,
            enable_user=settings.enable_user_level,
        )
        if not roots:
            continue

        mcp.add_provider(SkillsDirectoryProvider(roots=roots, supporting_files="resources"))

    # --- Bundled skills (shipped with this package, not affected by scope flags) ---
    if settings.enable_bundled and _BUNDLED_SKILLS_PATH.exists():
        mcp.add_provider(SkillsDirectoryProvider(roots=[_BUNDLED_SKILLS_PATH], supporting_files="resources"))

    # --- Extra directories (always included, not affected by scope flags) ---
    for extra in settings.extra_dirs:
        if not extra.path.exists():
            continue
        mcp.add_provider(SkillsDirectoryProvider(roots=[extra.path], supporting_files="resources"))

    # --- Tool: list_skills ---
    @mcp.tool(
        name="list_skills",
        description=(
            "List all available skills by name and description. "
            "Call this tool to discover which skills are loaded in this session. "
            "Each skill exposes its full content as MCP resources under skill://{name}/ — "
            "use get_skill to read the full instructions and all supporting files."
        ),
    )
    async def list_skills() -> str:
        """Return a summary of every available skill with name and description."""
        resources = await mcp.list_resources()
        lines: list[str] = []
        for resource in resources:
            uri = str(resource.uri)
            if uri.endswith("/SKILL.md"):
                skill_name = uri.removeprefix("skill://").removesuffix("/SKILL.md")
                lines.append(f"- **{skill_name}**: {resource.description}")
        if not lines:
            return "No skills are currently available."
        return "Available skills (use `get_skill` to load the full instructions):\n\n" + "\n".join(lines)

    # --- Tool: get_skill ---
    @mcp.tool(
        name="get_skill",
        description=(
            "Load the full instructions of a skill by name, including all supporting files. "
            "Use `list_skills` first to discover available skill names, "
            "then call this tool with the exact skill name to get the complete SKILL.md content "
            "together with every supporting file bundled in that skill. "
            "The content is the authoritative instructions you MUST follow for that task — "
            "read every section carefully before proceeding."
        ),
    )
    async def get_skill(name: str) -> str:
        """
        Args:
            name: Exact skill name as returned by list_skills (e.g. 'pytest-coverage').
        """
        prefix = f"skill://{name}/"
        all_resources = await mcp.list_resources()
        skill_uris = sorted(
            (str(r.uri) for r in all_resources if str(r.uri).startswith(prefix)),
            key=lambda u: (0 if u.endswith("/SKILL.md") else 1, u),
        )
        if not skill_uris:
            available = await list_skills()
            return f"Skill '{name}' not found.\n\n{available}"
        sections: list[str] = []
        for uri in skill_uris:
            relative_path = uri.removeprefix(prefix)
            try:
                resource_result = await mcp.read_resource(uri)
            except NotFoundError:
                continue
            file_parts: list[str] = []
            for content in resource_result.contents:
                if isinstance(content.content, str):
                    file_parts.append(content.content)
                elif isinstance(content.content, bytes):
                    file_parts.append(content.content.decode())
            if file_parts:
                file_body = "\n".join(file_parts)
                if relative_path == "SKILL.md":
                    sections.append(file_body)
                else:
                    sections.append(f"--- {relative_path} ---\n{file_body}")
        return "\n\n".join(sections)

    # --- Slash commands from agent native prompt files (cross-agent sharing) ---
    # Reads each agent's native command format and registers them as MCP prompts.
    # Workspace root and user home are passed according to scope flags.
    # First provider to define a name wins; "create-skill" is reserved.
    prompt_roots: list[Path] = []
    if settings.enable_workspace_level:
        prompt_roots.append(ws)
    if settings.enable_user_level:
        prompt_roots.append(Path.home())

    seen_prompt_names: set[str] = {"create-skill"}
    for provider in AGENT_PROVIDERS.values():
        for cmd in provider.list_prompts(roots=prompt_roots or None):
            if not isinstance(cmd, PromptSlashCommand):
                continue
            cmd_name = cmd.name.lstrip("/")
            if cmd_name in seen_prompt_names:
                continue
            seen_prompt_names.add(cmd_name)
            mcp.prompt(name=cmd_name, description=cmd.description)(_static_prompt(cmd.prompt))

    return mcp
