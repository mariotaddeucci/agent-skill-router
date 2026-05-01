"""Tests for agent setup providers and the setup CLI command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_skill_router.agents import AGENT_PROVIDERS, GitHubCopilotSetupProvider, OpenCodeSetupProvider
from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG, McpConfig
from agent_skill_router.cli import app

runner = CliRunner()


def test_default_mcp_config_shape() -> None:
    assert _DEFAULT_MCP_CONFIG.command == "uvx"
    assert "agent-skill-router" in _DEFAULT_MCP_CONFIG.args
    assert "run" in _DEFAULT_MCP_CONFIG.args


def test_all_providers_registered() -> None:
    expected = {"github-copilot", "claude", "cursor", "opencode", "goose", "gemini", "codex"}
    assert set(AGENT_PROVIDERS) == expected


def test_stub_providers_have_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

    for name, provider in AGENT_PROVIDERS.items():
        if name == "github-copilot":
            continue
        ws = provider.config_path_workspace()
        usr = provider.config_path_user()
        assert isinstance(ws, Path), f"{name}: workspace path must be a Path"
        assert isinstance(usr, Path), f"{name}: user path must be a Path"
        assert ws != usr, f"{name}: workspace and user paths must differ"


def test_stub_providers_raise_on_discover() -> None:
    for name, provider in AGENT_PROVIDERS.items():
        if name in {"github-copilot", "opencode"}:
            continue
        with pytest.raises(NotImplementedError):
            provider.discover()


def test_stub_providers_raise_on_install(tmp_path: Path) -> None:
    for name, provider in AGENT_PROVIDERS.items():
        if name in {"github-copilot", "opencode"}:
            continue
        with pytest.raises(NotImplementedError):
            provider.install(tmp_path / "config.json")


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


class TestSetupCommand:
    def test_setup_github_copilot_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["setup-mcp", "github-copilot"])

        assert result.exit_code == 0
        config = tmp_path / ".vscode" / "mcp.json"
        assert config.exists()
        data = json.loads(config.read_text())
        assert "agent-skill-router" in data["servers"]
        assert "workspace" in result.output

    def test_setup_github_copilot_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        result = runner.invoke(app, ["setup-mcp", "github-copilot", "--user"])

        assert result.exit_code == 0
        config = tmp_path / ".vscode" / "mcp.json"
        assert config.exists()
        assert "user" in result.output

    def test_setup_unknown_agent(self) -> None:
        result = runner.invoke(app, ["setup-mcp", "nonexistent-agent"])
        assert result.exit_code == 1
        assert "unknown agent" in result.output

    def test_setup_stub_agent_shows_manual_instructions(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["setup-mcp", "claude"])
        assert result.exit_code == 1
        assert "not supported" in result.output
        assert "claude" in result.output.lower()

    def test_setup_autodiscovery_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        result = runner.invoke(app, ["setup-mcp"])

        assert result.exit_code == 0
        assert "github-copilot" in result.output
        assert "workspace" in result.output

        config = tmp_path / ".vscode" / "mcp.json"
        assert config.exists()
        data = json.loads(config.read_text())
        assert "agent-skill-router" in data["servers"]

    def test_setup_autodiscovery_user(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

        result = runner.invoke(app, ["setup-mcp", "--user"])

        assert result.exit_code == 0
        assert "github-copilot" in result.output
        assert "user" in result.output

        config = fake_home / ".vscode" / "mcp.json"
        assert config.exists()
        data = json.loads(config.read_text())
        assert "agent-skill-router" in data["servers"]

    def test_setup_autodiscovery_no_supported_agents(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

        import agent_skill_router.cli as cli_mod

        monkeypatch.setattr(cli_mod, "AGENT_PROVIDERS", {})

        result = runner.invoke(app, ["setup-mcp"])
        assert result.exit_code == 0
        assert "automated setup" in result.output
