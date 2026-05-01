"""Integration tests for AgentSetupProvider.discover()."""

import shutil
from pathlib import Path

import pytest

from agent_skill_router.agents import AGENT_PROVIDERS


def test_discover_empty_when_no_configs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All providers return [] in a clean directory with no config files."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))

    for name, provider in AGENT_PROVIDERS.items():
        result = provider.discover()
        assert result == [], f"{name}: expected [] in empty workspace, got {result}"


def test_discover_finds_workspace_configs(workspace: Path) -> None:
    """Each provider discovers its workspace config from the fixture."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.discover()
        assert len(result) >= 1, f"{name}: expected at least 1 workspace config"
        for path in result:
            assert path.exists(), f"{name}: discovered path does not exist: {path}"
            assert path.is_file(), f"{name}: discovered path is not a file: {path}"


def test_discover_all_paths_are_within_workspace(workspace: Path) -> None:
    """Discovered workspace paths live under the workspace root (not home)."""
    for name, provider in AGENT_PROVIDERS.items():
        ws_path = provider.config_path_workspace()
        result = provider.discover()
        if result:
            assert ws_path in result, f"{name}: workspace config {ws_path} not in discovered list {result}"


def test_discover_finds_user_config_when_present(workspace: Path) -> None:
    """When a user-scope config exists, discover() includes it alongside workspace."""
    for name, provider in AGENT_PROVIDERS.items():
        user_path = provider.config_path_user()
        ws_path = provider.config_path_workspace()

        if not ws_path.exists():
            continue

        user_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ws_path, user_path)

        result = provider.discover()
        assert user_path in result, f"{name}: user config {user_path} not discovered after creation"
        assert ws_path in result, f"{name}: workspace config {ws_path} missing after adding user config"


def test_discover_returns_list_of_paths(workspace: Path) -> None:
    """discover() always returns list[Path], never None or other type."""
    for name, provider in AGENT_PROVIDERS.items():
        result = provider.discover()
        assert isinstance(result, list), f"{name}: discover() must return list"
        for item in result:
            assert isinstance(item, Path), f"{name}: each item must be Path, got {type(item)}"
