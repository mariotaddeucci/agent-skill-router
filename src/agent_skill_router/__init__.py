from .server import build_mcp
from .settings import Settings


def main() -> None:
    settings = Settings()
    mcp = build_mcp(settings)
    mcp.run()


__all__ = ["Settings", "build_mcp", "main"]
