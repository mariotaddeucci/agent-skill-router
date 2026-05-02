"""Tests for CodexSetupProvider."""

import tomllib
from pathlib import Path

import pytest

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, McpConfig
from agent_skill_router.agents.codex import CodexSetupProvider


class TestCodexSetupProvider:
    def setup_method(self) -> None:
        self.provider = CodexSetupProvider()

    def test_config_path_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert self.provider.config_path_workspace() == tmp_path / ".codex" / "config.toml"

    def test_config_path_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        assert self.provider.config_path_user() == tmp_path / ".codex" / "config.toml"

    def test_discover_returns_empty_when_no_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
        assert self.provider.discover() == []

    def test_discover_returns_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        ws = tmp_path / ".codex" / "config.toml"
        ws.parent.mkdir(parents=True)
        ws.write_text("")
        assert self.provider.discover() == [ws]

        usr = tmp_path / "home" / ".codex" / "config.toml"
        usr.parent.mkdir(parents=True)
        usr.write_text("")
        assert set(self.provider.discover()) == {ws, usr}

    def test_install_creates_file_with_entry(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        self.provider.install(config)

        data = tomllib.loads(config.read_text())
        entry = data["mcp_servers"]["agent-skill-router"]
        assert entry["command"] == _DEFAULT_MCP_CONFIG.command
        assert entry["args"] == _DEFAULT_MCP_CONFIG.args

    def test_install_merges_existing_servers(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        config.parent.mkdir(parents=True)
        config.write_text('[mcp_servers.other]\ncommand = "foo"\nargs = []\n')

        self.provider.install(config)

        data = tomllib.loads(config.read_text())
        assert "other" in data["mcp_servers"]
        assert "agent-skill-router" in data["mcp_servers"]

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        self.provider.install(config)
        first = config.read_text()
        self.provider.install(config)
        assert config.read_text() == first

    def test_install_custom_mcp_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        custom = McpConfig(command="python", args=["-m", "my_mcp"])
        self.provider.install(config, mcp_config=custom)

        data = tomllib.loads(config.read_text())
        entry = data["mcp_servers"]["agent-skill-router"]
        assert entry["command"] == "python"
        assert entry["args"] == ["-m", "my_mcp"]

    def test_install_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = tmp_path / "deep" / "nested" / "config.toml"
        self.provider.install(config)
        assert config.exists()

    def test_read_mcp_servers_returns_empty_when_no_config(self, tmp_path: Path) -> None:
        result = self.provider.read_mcp_servers(roots=[tmp_path])
        assert result == {}

    def test_read_mcp_servers_parses_mcp_servers_section(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        config.parent.mkdir(parents=True)
        config.write_text('[mcp_servers.my-server]\ncommand = "uvx"\nargs = ["my-pkg"]\n')

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "my-server" in result
        assert result["my-server"].command == "uvx"
        assert result["my-server"].args == ["my-pkg"]

    def test_read_mcp_servers_excludes_self(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        config.parent.mkdir(parents=True)
        config.write_text(
            '[mcp_servers.agent-skill-router]\ncommand = "uvx"\nargs = []\n\n'
            '[mcp_servers.other-server]\ncommand = "node"\nargs = ["server.js"]\n'
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "agent-skill-router" not in result
        assert "other-server" in result

    def test_read_mcp_servers_skips_corrupt_toml(self, tmp_path: Path) -> None:
        config = tmp_path / ".codex" / "config.toml"
        config.parent.mkdir(parents=True)
        config.write_text("NOT VALID TOML [[[")

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert result == {}
