"""Tests for OpenCodeSetupProvider."""

import json
from pathlib import Path

import pytest

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG
from agent_skill_router.agents.opencode import OpenCodeSetupProvider


class TestOpenCodeSetupProvider:
    def setup_method(self) -> None:
        self.provider = OpenCodeSetupProvider()

    def test_config_path_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert self.provider.config_path_workspace() == tmp_path / ".opencode" / "mcp.json"

    def test_config_path_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        assert self.provider.config_path_user() == tmp_path / ".config" / "opencode" / "opencode.json"

    def test_discover_returns_empty_when_no_config_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
        assert self.provider.discover() == []

    def test_discover_returns_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        ws = tmp_path / ".opencode" / "mcp.json"
        ws.parent.mkdir(parents=True)
        ws.write_text("{}\n")
        assert self.provider.discover() == [ws]

        usr = tmp_path / "home" / ".config" / "opencode" / "opencode.json"
        usr.parent.mkdir(parents=True)
        usr.write_text("{}\n")
        assert set(self.provider.discover()) == {ws, usr}

    def test_install_creates_new_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".opencode" / "mcp.json"
        self.provider.install(config)

        data = json.loads(config.read_text())
        entry = data["mcp"]["agent-skill-router"]
        assert entry["type"] == "local"
        assert entry["enabled"] is True
        assert entry["command"][0] == _DEFAULT_MCP_CONFIG.command
        assert entry["command"][1:] == _DEFAULT_MCP_CONFIG.args

    def test_install_merges_existing_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".opencode" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"mcp": {"other": {"type": "local", "command": ["foo"], "enabled": True}}}))

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert "other" in data["mcp"]
        assert "agent-skill-router" in data["mcp"]

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        config = tmp_path / ".opencode" / "mcp.json"
        self.provider.install(config)
        first = config.read_text()
        self.provider.install(config)
        assert config.read_text() == first

    def test_install_preserves_existing_top_level_keys(self, tmp_path: Path) -> None:
        config = tmp_path / ".opencode" / "opencode.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"theme": "dark", "model": "gpt-4"}))

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert data["theme"] == "dark"
        assert data["model"] == "gpt-4"
        assert "agent-skill-router" in data["mcp"]

    def test_read_mcp_servers_returns_empty_when_no_config(self, tmp_path: Path) -> None:
        result = self.provider.read_mcp_servers(roots=[tmp_path])
        assert result == {}

    def test_read_mcp_servers_parses_workspace_mcp_key(self, tmp_path: Path) -> None:
        config = tmp_path / ".opencode" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps(
                {
                    "mcp": {
                        "ws-server": {
                            "type": "local",
                            "command": ["uvx", "pkg"],
                            "enabled": True,
                        }
                    }
                }
            )
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "ws-server" in result
        assert result["ws-server"].command == "uvx"
        assert result["ws-server"].args == ["pkg"]

    def test_read_mcp_servers_parses_user_opencode_json(self, tmp_path: Path) -> None:
        config = tmp_path / ".config" / "opencode" / "opencode.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps(
                {
                    "mcp": {
                        "my-tool": {
                            "type": "local",
                            "command": ["uvx", "my-pkg", "run"],
                            "enabled": True,
                        }
                    }
                }
            )
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "my-tool" in result
        assert result["my-tool"].command == "uvx"
        assert result["my-tool"].args == ["my-pkg", "run"]

    def test_read_mcp_servers_excludes_self(self, tmp_path: Path) -> None:
        config = tmp_path / ".config" / "opencode" / "opencode.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps(
                {
                    "mcp": {
                        "agent-skill-router": {
                            "type": "local",
                            "command": ["uv", "run", "agent-skill-router", "run"],
                            "enabled": True,
                        },
                        "other": {
                            "type": "local",
                            "command": ["uvx", "other-pkg"],
                            "enabled": True,
                        },
                    }
                }
            )
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "agent-skill-router" not in result
        assert "other" in result

    def test_read_mcp_servers_skips_corrupt_json(self, tmp_path: Path) -> None:
        config = tmp_path / ".config" / "opencode" / "opencode.json"
        config.parent.mkdir(parents=True)
        config.write_text("NOT JSON")

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert result == {}
