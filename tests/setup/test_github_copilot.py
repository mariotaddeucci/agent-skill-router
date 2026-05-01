"""Tests for GitHubCopilotSetupProvider."""

import json
from pathlib import Path

import pytest

from agent_skill_router.agents import GitHubCopilotSetupProvider
from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, McpConfig


class TestGitHubCopilotSetupProvider:
    def setup_method(self) -> None:
        self.provider = GitHubCopilotSetupProvider()

    def test_config_path_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert self.provider.config_path_workspace() == tmp_path / ".vscode" / "mcp.json"

    def test_config_path_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        assert self.provider.config_path_user() == tmp_path / ".vscode" / "mcp.json"

    def test_config_path_respects_user_flag(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
        assert self.provider.config_path(user=False) == tmp_path / ".vscode" / "mcp.json"
        assert self.provider.config_path(user=True) == tmp_path / "home" / ".vscode" / "mcp.json"

    def test_discover_returns_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        assert self.provider.discover() == []

        ws = tmp_path / ".vscode" / "mcp.json"
        ws.parent.mkdir(parents=True)
        ws.write_text("{}\n")
        assert self.provider.discover() == [ws]

        usr = tmp_path / "home" / ".vscode" / "mcp.json"
        usr.parent.mkdir(parents=True)
        usr.write_text("{}\n")
        assert set(self.provider.discover()) == {ws, usr}

    def test_install_creates_file_with_entry(self, tmp_path: Path) -> None:
        config = tmp_path / ".vscode" / "mcp.json"
        self.provider.install(config)

        data = json.loads(config.read_text())
        entry = data["servers"]["agent-skill-router"]
        assert entry["type"] == "stdio"
        assert entry["command"] == _DEFAULT_MCP_CONFIG.command
        assert entry["args"] == _DEFAULT_MCP_CONFIG.args

    def test_install_merges_existing_servers(self, tmp_path: Path) -> None:
        config = tmp_path / ".vscode" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"servers": {"other-mcp": {"type": "stdio", "command": "foo", "args": []}}}))

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert "other-mcp" in data["servers"]
        assert "agent-skill-router" in data["servers"]

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        config = tmp_path / ".vscode" / "mcp.json"
        self.provider.install(config)
        self.provider.install(config)

        data = json.loads(config.read_text())
        assert len(data["servers"]) == 1

    def test_install_custom_mcp_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".vscode" / "mcp.json"
        custom = McpConfig(command="python", args=["-m", "my_mcp"])
        self.provider.install(config, mcp_config=custom)

        data = json.loads(config.read_text())
        entry = data["servers"]["agent-skill-router"]
        assert entry["command"] == "python"
        assert entry["args"] == ["-m", "my_mcp"]

    def test_install_recovers_from_corrupt_json(self, tmp_path: Path) -> None:
        config = tmp_path / ".vscode" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text("NOT VALID JSON")

        self.provider.install(config)

        data = json.loads(config.read_text())
        assert "agent-skill-router" in data["servers"]

    def test_install_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = tmp_path / "deep" / "nested" / "mcp.json"
        self.provider.install(config)
        assert config.exists()
