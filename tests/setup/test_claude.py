"""Tests for ClaudeSetupProvider."""

import json
from pathlib import Path

import pytest

from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG
from agent_skill_router.agents.claude import ClaudeSetupProvider


class TestClaudeSetupProvider:
    def setup_method(self) -> None:
        self.provider = ClaudeSetupProvider()

    def test_config_path_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert self.provider.config_path_workspace() == tmp_path / ".claude" / "mcp.json"

    def test_config_path_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        assert self.provider.config_path_user() == tmp_path / ".claude" / "mcp.json"

    def test_discover_returns_empty_when_no_config_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
        assert self.provider.discover() == []

    def test_discover_returns_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        ws = tmp_path / ".claude" / "mcp.json"
        ws.parent.mkdir(parents=True)
        ws.write_text("{}\n")
        assert self.provider.discover() == [ws]

        usr = tmp_path / "home" / ".claude" / "mcp.json"
        usr.parent.mkdir(parents=True)
        usr.write_text("{}\n")
        assert set(self.provider.discover()) == {ws, usr}

    def test_install_creates_new_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
        self.provider.install(config)

        data = json.loads(config.read_text())
        entry = data["mcpServers"]["agent-skill-router"]
        assert entry["type"] == "stdio"
        assert entry["command"] == _DEFAULT_MCP_CONFIG.command
        assert entry["args"] == _DEFAULT_MCP_CONFIG.args

    def test_install_merges_existing_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"mcpServers": {"other": {}}}))

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert "other" in data["mcpServers"]
        assert "agent-skill-router" in data["mcpServers"]

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
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
        config = tmp_path / ".claude" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"mcpServers": {"my-server": {"command": "uvx", "args": ["my-pkg"]}}}))

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "my-server" in result
        assert result["my-server"].command == "uvx"
        assert result["my-server"].args == ["my-pkg"]

    def test_read_mcp_servers_excludes_self(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
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

    def test_read_mcp_servers_first_wins_across_roots(self, tmp_path: Path) -> None:
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        for root in (root1, root2):
            cfg = root / ".claude" / "mcp.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(json.dumps({"mcpServers": {"dup-server": {"command": f"cmd-{root.name}", "args": []}}}))

        result = self.provider.read_mcp_servers(roots=[root1, root2])

        assert result["dup-server"].command == "cmd-root1"

    def test_read_mcp_servers_skips_corrupt_json(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text("NOT JSON")

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert result == {}

    def test_read_mcp_servers_includes_env(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "env-server": {
                            "command": "uvx",
                            "args": [],
                            "env": {"MY_VAR": "value"},
                        }
                    }
                }
            )
        )

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert result["env-server"].env == {"MY_VAR": "value"}

    def test_read_mcp_servers_parses_url_entry(self, tmp_path: Path) -> None:
        config = tmp_path / ".claude" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"mcpServers": {"remote": {"url": "https://example.com/mcp"}}}))

        result = self.provider.read_mcp_servers(roots=[tmp_path])

        assert "remote" in result
        assert result["remote"].url == "https://example.com/mcp"
        assert result["remote"].command is None
