"""CLI for agent-skill-router: list, install, run, and setup-mcp commands."""

from pathlib import Path
from typing import Annotated

import typer

from agent_skill_router._skills import discover_skills, install_skill
from agent_skill_router.agents import AGENT_PROVIDERS
from agent_skill_router.server import _BUNDLED_SKILLS_PATH, _PROVIDER_ROOTS, _resolve_roots
from agent_skill_router.settings import Settings

app = typer.Typer(
    name="agent-skill-router",
    help="Manage agent skills and run the MCP server.",
    no_args_is_help=True,
)


def _all_roots(settings: Settings) -> list[Path]:
    """Return all skill roots that would be used by build_mcp, in discovery order."""
    roots: list[Path] = []
    for attr, _cls, roots_by_level in _PROVIDER_ROOTS:
        if not getattr(settings, attr):
            continue
        roots.extend(
            _resolve_roots(
                roots_by_level,
                enable_workspace=settings.enable_workspace_level,
                enable_user=settings.enable_user_level,
            )
        )
    if settings.enable_bundled and _BUNDLED_SKILLS_PATH.exists():
        roots.append(_BUNDLED_SKILLS_PATH)
    for extra in settings.extra_dirs:
        if extra.path.exists():
            roots.append(extra.path)
    return roots


@app.command()
def list(
    user: Annotated[
        bool, typer.Option("--user", help="Show only user-level skills (~/.agents/skills/ and equivalents).")
    ] = False,
    workspace: Annotated[
        bool, typer.Option("--workspace", help="Show only workspace-level skills (.agents/skills/ and equivalents).")
    ] = False,
) -> None:
    """List all skills accessible to the MCP server.

    Discovers skills from every enabled provider root (workspace and/or user level)
    and prints a table with each skill's name, directory, and description.
    Use --user or --workspace to restrict the scope.
    """
    settings = Settings(
        enable_workspace_level=not user if (user or workspace) else True,
        enable_user_level=not workspace if (user or workspace) else True,
    )

    roots = _all_roots(settings)
    skills = discover_skills(roots)

    if not skills:
        typer.echo("No skills found.")
        raise typer.Exit()

    name_w = max(len(s.name) for s in skills)
    dir_w = max(len(str(s.directory)) for s in skills)

    header = f"{'NAME':<{name_w}}  {'DIRECTORY':<{dir_w}}  DESCRIPTION"
    typer.echo(header)
    typer.echo("-" * len(header))
    for skill in skills:
        typer.echo(f"{skill.name:<{name_w}}  {skill.directory!s:<{dir_w}}  {skill.description}")


@app.command()
def install(
    source: Annotated[
        Path, typer.Argument(help="Path to the skill directory to install. Must contain a SKILL.md file.")
    ],
    user: Annotated[
        bool,
        typer.Option(
            "--user",
            help="Install to ~/.agents/skills/ (available across all workspaces). Default: .agents/skills/ in the current directory.",
        ),
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite the skill if it already exists at the destination.")
    ] = False,
) -> None:
    """Install a skill into the local or user-level skills directory.

    Copies the skill directory into .agents/skills/ (workspace) or
    ~/.agents/skills/ (user, with --user). The destination is created
    automatically if it does not exist. Use --force to replace an existing skill.
    """
    dest_root = Path.home() / ".agents" / "skills" if user else Path.cwd() / ".agents" / "skills"

    source = source.resolve()

    if not source.exists():
        typer.echo(f"Error: {source} does not exist.", err=True)
        raise typer.Exit(code=1)

    if force:
        dest = dest_root / source.name
        if dest.exists():
            import shutil

            shutil.rmtree(dest)

    try:
        installed = install_skill(source, dest_root)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except FileExistsError as exc:
        typer.echo(
            f"Error: skill '{source.name}' already exists at {exc}. Use --force to overwrite.",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    scope = "user (~/.agents/skills/)" if user else "workspace (.agents/skills/)"
    typer.echo(f"Installed '{source.name}' to {installed}  [{scope}]")


@app.command()
def run() -> None:
    """Start the Agent Skill Router MCP server.

    Reads configuration from SKILL_ROUTER_* environment variables and starts
    the MCP server over stdio, making all discovered skills available to connected agents.
    """
    from agent_skill_router.server import build_mcp

    settings = Settings()
    mcp = build_mcp(settings)
    mcp.run()


@app.command(name="setup-mcp")
def setup(
    agent: Annotated[
        str | None,
        typer.Argument(
            help=(
                "Agent to configure (e.g. github-copilot). "
                f"Available: {', '.join(AGENT_PROVIDERS)}. "
                "Omit to auto-discover all installed agents."
            ),
        ),
    ] = None,
    user: Annotated[
        bool,
        typer.Option("--user", help="Write to the user-scoped config file instead of the workspace one."),
    ] = False,
) -> None:
    """Add the Agent Skill Router MCP server to an agent's config.

    When AGENT is provided, configures only that agent. When omitted, each
    provider that supports auto-discovery is queried and all detected config
    files are updated automatically.

    Use --user to write to the user-level config file (applies across all
    workspaces) instead of the workspace-local one.
    """
    if agent is not None:
        provider = AGENT_PROVIDERS.get(agent)
        if provider is None:
            available = ", ".join(sorted(AGENT_PROVIDERS))
            typer.echo(f"Error: unknown agent '{agent}'. Available: {available}", err=True)
            raise typer.Exit(code=1)

        try:
            config_path = provider.config_path(user=user)
            provider.install(config_path)
        except NotImplementedError:
            scope = "user" if user else "workspace"
            config_path = provider.config_path(user=user)
            typer.echo(
                f"Automated setup is not supported for '{agent}'.\n"
                f"Add the MCP server manually to: {config_path}  [{scope}]"
            )
            raise typer.Exit(code=1) from None

        scope_label = "user" if user else "workspace"
        typer.echo(f"Configured '{agent}' MCP server in {config_path}  [{scope_label}]")
        return

    # Auto-discovery mode: install into the appropriate scope for every
    # provider that supports automated install.
    installed_any = False
    for provider in AGENT_PROVIDERS.values():
        config_path = provider.config_path(user=user)
        try:
            provider.install(config_path)
            scope_label = "user" if user else "workspace"
            typer.echo(f"Configured '{provider.name}' MCP server in {config_path}  [{scope_label}]")
            installed_any = True
        except NotImplementedError:
            continue

    if not installed_any:
        typer.echo(
            "No agents with automated setup were found.\n"
            f"Run with a specific agent: agent-skill-router setup-mcp --agent <name>\n"
            f"Available agents: {', '.join(sorted(AGENT_PROVIDERS))}"
        )


def main() -> None:
    """Entry point used by the project script."""
    app()
