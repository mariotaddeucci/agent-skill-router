"""Tests for GooseSetupProvider."""

import json
from pathlib import Path

import pytest

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG
from agent_skill_router.agents.goose import GooseSetupProvider


class TestGooseSetupProvider:
    def setup_method(self) -> None:
        self.provider = GooseSetupProvider()

    def test_config_path_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert self.provider.config_path_workspace() == tmp_path / ".goose" / "mcp.json"

    def test_config_path_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        assert self.provider.config_path_user() == tmp_path / ".config" / "goose" / "config.yaml"

    def test_discover_returns_empty_when_no_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
        assert self.provider.discover() == []

    def test_discover_returns_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        ws = tmp_path / ".goose" / "mcp.json"
        ws.parent.mkdir(parents=True)
        ws.write_text("{}\n")
        assert self.provider.discover() == [ws]

        usr = tmp_path / "home" / ".config" / "goose" / "config.yaml"
        usr.parent.mkdir(parents=True)
        usr.write_text("")
        assert set(self.provider.discover()) == {ws, usr}

    def test_install_workspace_creates_json_entry(self, tmp_path: Path) -> None:
        config = tmp_path / ".goose" / "mcp.json"
        self.provider.install(config)

        data = json.loads(config.read_text())
        entry = data["mcpServers"]["agent-skill-router"]
        assert entry["command"] == _DEFAULT_MCP_CONFIG.command
        assert entry["args"] == _DEFAULT_MCP_CONFIG.args

    def test_install_user_creates_yaml_entry(self, tmp_path: Path) -> None:
        config = tmp_path / ".config" / "goose" / "config.yaml"
        self.provider.install(config)

        content = config.read_text()
        assert "agent-skill-router" in content
        assert "extensions" in content

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        config = tmp_path / ".goose" / "mcp.json"
        self.provider.install(config)
        first = config.read_text()
        self.provider.install(config)
        assert config.read_text() == first

    def test_install_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = tmp_path / "deep" / "nested" / "mcp.json"
        self.provider.install(config)
        assert config.exists()

    def test_read_mcp_servers_returns_empty_when_no_config(self, tmp_path: Path) -> None:
        result = self.provider.read_mcp_servers(roots=[tmp_path])
        assert result == {}

    def test_read_mcp_servers_parses_mcpservers_key(self, tmp_path: Path) -> None:
        config = tmp_path / ".goose" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps({"mcpServers": {"my-server": {"type": "stdio", "command": "uvx", "args": ["my-pkg"]}}})
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "my-server" in result
        assert result["my-server"].command == "uvx"
        assert result["my-server"].args == ["my-pkg"]

    def test_read_mcp_servers_excludes_self(self, tmp_path: Path) -> None:
        config = tmp_path / ".goose" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "agent-skill-router": {"command": "uvx", "args": []},
                        "other-server": {"command": "node", "args": ["server.js"]},
                    }
                }
            )
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "agent-skill-router" not in result
        assert "other-server" in result

    def test_read_mcp_servers_skips_corrupt_json(self, tmp_path: Path) -> None:
        config = tmp_path / ".goose" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text("NOT JSON")

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert result == {}
