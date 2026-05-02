"""Tests for Settings — env var parsing, defaults, and validation."""

from agent_skill_router.settings import ExtraDirectory, Settings


def test_defaults_all_enabled():
    s = Settings()
    assert s.enable_workspace_level is True
    assert s.enable_user_level is True
    assert s.enable_bundled is True
    assert s.providers_default is True
    # raw values are None (unset) — effective value resolves via providers_default
    assert s.enable_claude is None
    assert s.enable_cursor is None
    # effective state is True (providers_default=True)
    assert s.is_provider_enabled("enable_claude") is True
    assert s.is_provider_enabled("enable_cursor") is True
    assert s.is_provider_enabled("enable_vscode") is True
    assert s.is_provider_enabled("enable_codex") is True
    assert s.is_provider_enabled("enable_gemini") is True
    assert s.is_provider_enabled("enable_goose") is True
    assert s.is_provider_enabled("enable_github_copilot") is True
    assert s.is_provider_enabled("enable_opencode") is True
    assert s.is_provider_enabled("enable_agents") is True
    assert s.is_provider_enabled("enable_openclaw") is True
    assert s.extra_dirs == []


def test_env_prefix_disables_provider(monkeypatch):
    monkeypatch.setenv("SKILL_ROUTER_ENABLE_CLAUDE", "false")
    s = Settings()
    assert s.enable_claude is False
    assert s.is_provider_enabled("enable_claude") is False
    # others stay enabled via providers_default
    assert s.enable_cursor is None
    assert s.is_provider_enabled("enable_cursor") is True


def test_providers_default_false_disables_all(monkeypatch):
    monkeypatch.setenv("SKILL_ROUTER_PROVIDERS_DEFAULT", "false")
    s = Settings()
    assert s.providers_default is False
    assert s.is_provider_enabled("enable_claude") is False
    assert s.is_provider_enabled("enable_cursor") is False
    assert s.is_provider_enabled("enable_agents") is False


def test_providers_default_false_with_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("SKILL_ROUTER_PROVIDERS_DEFAULT", "false")
    monkeypatch.setenv("SKILL_ROUTER_ENABLE_AGENTS", "true")
    s = Settings()
    assert s.providers_default is False
    assert s.is_provider_enabled("enable_agents") is True
    assert s.is_provider_enabled("enable_claude") is False
    assert s.is_provider_enabled("enable_cursor") is False


def test_env_prefix_disables_scope(monkeypatch):
    monkeypatch.setenv("SKILL_ROUTER_ENABLE_WORKSPACE_LEVEL", "false")
    monkeypatch.setenv("SKILL_ROUTER_ENABLE_USER_LEVEL", "false")
    s = Settings()
    assert s.enable_workspace_level is False
    assert s.enable_user_level is False


def test_env_prefix_disables_bundled(monkeypatch):
    monkeypatch.setenv("SKILL_ROUTER_ENABLE_BUNDLED", "false")
    s = Settings()
    assert s.enable_bundled is False


def test_extra_dirs_parsed_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "SKILL_ROUTER_EXTRA_DIRS",
        f'[{{"path": "{tmp_path}"}}]',
    )
    s = Settings()
    assert len(s.extra_dirs) == 1
    assert s.extra_dirs[0].path == tmp_path


def test_extra_dirs_empty_by_default():
    s = Settings()
    assert s.extra_dirs == []


def test_extra_directory_requires_path(tmp_path):
    ed = ExtraDirectory(path=tmp_path)
    assert ed.path == tmp_path


def test_settings_constructed_directly():
    s = Settings(enable_claude=False, enable_gemini=False)
    assert s.enable_claude is False
    assert s.enable_gemini is False
    assert s.is_provider_enabled("enable_claude") is False
    assert s.is_provider_enabled("enable_gemini") is False
    # cursor not set — resolves to providers_default (True)
    assert s.enable_cursor is None
    assert s.is_provider_enabled("enable_cursor") is True
