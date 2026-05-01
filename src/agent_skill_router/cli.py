"""CLI for agent-skill-router: list, install, and run the MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agent_skill_router._skills import discover_skills, install_skill
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
    user: Annotated[bool, typer.Option("--user", help="Show user-level skills only.")] = False,
    workspace: Annotated[bool, typer.Option("--workspace", help="Show workspace-level skills only.")] = False,
) -> None:
    """List all skills accessible to the MCP server."""
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
    source: Annotated[Path, typer.Argument(help="Path to the skill directory to install.")],
    user: Annotated[
        bool,
        typer.Option("--user", help="Install to ~/.agents/skills/ (global). Default: .agents/skills/ in cwd."),
    ] = False,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite if skill already exists.")] = False,
) -> None:
    """Install a skill into the local or user-level skills directory."""
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
    """Start the Agent Skill Router MCP server."""
    from agent_skill_router.server import build_mcp

    settings = Settings()
    mcp = build_mcp(settings)
    mcp.run()


def main() -> None:
    """Entry point used by the project script."""
    app()
