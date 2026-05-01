"""Tests for agent setup providers and the setup CLI command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_skill_router.agents import AGENT_PROVIDERS
from agent_skill_router.agents._base import _DEFAULT_MCP_CONFIG
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
        if name in {"github-copilot", "claude", "opencode"}:
            continue
        with pytest.raises(NotImplementedError):
            provider.discover()


def test_stub_providers_raise_on_install(tmp_path: Path) -> None:
    for name, provider in AGENT_PROVIDERS.items():
        if name in {"github-copilot", "claude", "opencode"}:
            continue
        with pytest.raises(NotImplementedError):
            provider.install(tmp_path / "config.json")


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
        result = runner.invoke(app, ["setup-mcp", "cursor"])
        assert result.exit_code == 1
        assert "not supported" in result.output
        assert "cursor" in result.output.lower()

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
