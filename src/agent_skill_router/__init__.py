from .cli import app
from .server import build_mcp
from .settings import Settings


def main() -> None:
    """Entry point: delegates to the Typer CLI app."""
    app()


__all__ = ["Settings", "app", "build_mcp", "main"]
