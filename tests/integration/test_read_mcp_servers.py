"""Integration tests for AgentSetupProvider.read_mcp_servers()."""

from pathlib import Path

import pytest

from agent_skill_router.agents import AGENT_PROVIDERS
from agent_skill_router.agents._base import NormalizedMcpServer


def test_read_mcp_servers_returns_empty_in_clean_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All providers return {} when no config files exist."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

    for name, provider in AGENT_PROVIDERS.items():
        result = provider.read_mcp_servers(roots=[tmp_path])
        assert result == {}, f"{name}: expected {{}} in empty workspace, got {result}"


def test_read_mcp_servers_returns_dict_of_normalized_servers(workspace: Path) -> None:
    """All providers return dict[str, NormalizedMcpServer] in fixture workspace."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.read_mcp_servers(roots=[workspace])
        assert isinstance(result, dict), f"{name}: read_mcp_servers must return dict"
        for server_name, server in result.items():
            assert isinstance(server_name, str), f"{name}: keys must be str"
            assert isinstance(server, NormalizedMcpServer), f"{name}: values must be NormalizedMcpServer"


def test_read_mcp_servers_discovers_existing_tool(workspace: Path) -> None:
    """All providers in the fixture workspace find the 'existing-tool' entry."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.read_mcp_servers(roots=[workspace])
        assert "existing-tool" in result, f"{name}: expected 'existing-tool' in {list(result)}"
        server = result["existing-tool"]
        assert server.command == "existing" or server.url is not None, f"{name}: unexpected server config: {server}"


def test_read_mcp_servers_never_returns_self(workspace: Path) -> None:
    """No provider should ever return 'agent-skill-router' in its server dict."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.read_mcp_servers(roots=[workspace])
        assert "agent-skill-router" not in result, (
            f"{name}: 'agent-skill-router' must not appear in read_mcp_servers output"
        )
