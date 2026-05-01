from agent_skill_router.cli import app
from agent_skill_router.server import build_mcp
from agent_skill_router.settings import Settings


def main() -> None:
    """Entry point: delegates to the Typer CLI app."""
    app()


__all__ = ["Settings", "app", "build_mcp", "main"]
