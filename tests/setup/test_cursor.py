"""Tests for CursorSetupProvider."""

import json
from pathlib import Path

import pytest

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, McpConfig
from agent_skill_router.agents.cursor import CursorSetupProvider


class TestCursorSetupProvider:
    def setup_method(self) -> None:
        self.provider = CursorSetupProvider()

    def test_config_path_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert self.provider.config_path_workspace() == tmp_path / ".cursor" / "mcp.json"

    def test_config_path_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        assert self.provider.config_path_user() == tmp_path / ".cursor" / "mcp.json"

    def test_discover_returns_empty_when_no_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
        assert self.provider.discover() == []

    def test_discover_returns_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        ws = tmp_path / ".cursor" / "mcp.json"
        ws.parent.mkdir(parents=True)
        ws.write_text("{}\n")
        assert self.provider.discover() == [ws]

        usr = tmp_path / "home" / ".cursor" / "mcp.json"
        usr.parent.mkdir(parents=True)
        usr.write_text("{}\n")
        assert set(self.provider.discover()) == {ws, usr}

    def test_install_creates_file_with_entry(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
        self.provider.install(config)

        data = json.loads(config.read_text())
        entry = data["mcpServers"]["agent-skill-router"]
        assert entry["command"] == _DEFAULT_MCP_CONFIG.command
        assert entry["args"] == _DEFAULT_MCP_CONFIG.args

    def test_install_merges_existing_servers(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"mcpServers": {"other-mcp": {"command": "foo", "args": []}}}))

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert "other-mcp" in data["mcpServers"]
        assert "agent-skill-router" in data["mcpServers"]

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
        self.provider.install(config)
        self.provider.install(config)

        data = json.loads(config.read_text())
        assert len(data["mcpServers"]) == 1

    def test_install_custom_mcp_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
        custom = McpConfig(command="python", args=["-m", "my_mcp"])
        self.provider.install(config, mcp_config=custom)

        data = json.loads(config.read_text())
        entry = data["mcpServers"]["agent-skill-router"]
        assert entry["command"] == "python"
        assert entry["args"] == ["-m", "my_mcp"]

    def test_install_recovers_from_corrupt_json(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text("NOT VALID JSON")

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert "agent-skill-router" in data["mcpServers"]

    def test_install_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = tmp_path / "deep" / "nested" / "mcp.json"
        self.provider.install(config)
        assert config.exists()

    def test_read_mcp_servers_returns_empty_when_no_config(self, tmp_path: Path) -> None:
        result = self.provider.read_mcp_servers(roots=[tmp_path])
        assert result == {}

    def test_read_mcp_servers_parses_mcpservers_key(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"mcpServers": {"my-server": {"command": "uvx", "args": ["my-pkg"]}}}))

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "my-server" in result
        assert result["my-server"].command == "uvx"
        assert result["my-server"].args == ["my-pkg"]

    def test_read_mcp_servers_excludes_self(self, tmp_path: Path) -> None:
        config = tmp_path / ".cursor" / "mcp.json"
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
        config = tmp_path / ".cursor" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text("NOT JSON")

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert result == {}
