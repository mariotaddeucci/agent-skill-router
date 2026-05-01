"""Tests for CLI commands: list, install, run."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

import agent_skill_router.cli as cli_mod
from agent_skill_router._skills import discover_skills, install_skill
from agent_skill_router.cli import app

runner = CliRunner()


def test_discover_skills_finds_valid_skill(tmp_path):
    skill = tmp_path / "my-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\ndescription: Does things\n---\n# My Skill\n")

    entries = discover_skills([tmp_path])
    assert len(entries) == 1
    assert entries[0].name == "my-skill"
    assert entries[0].description == "Does things"
    assert entries[0].directory == skill


def test_discover_skills_skips_dirs_without_skill_md(tmp_path):
    (tmp_path / "not-a-skill").mkdir()
    assert discover_skills([tmp_path]) == []


def test_discover_skills_skips_nonexistent_root(tmp_path):
    assert discover_skills([tmp_path / "ghost"]) == []


def test_discover_skills_deduplication_first_wins(tmp_path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    for root in (root_a, root_b):
        root.mkdir()
        skill = root / "shared-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(f"---\ndescription: From {root.name}\n---\n")

    entries = discover_skills([root_a, root_b])
    assert len(entries) == 1
    assert entries[0].description == "From a"


def test_discover_skills_no_description_fallback(tmp_path):
    skill = tmp_path / "bare-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# No frontmatter\n")

    entries = discover_skills([tmp_path])
    assert entries[0].description == ""


def test_install_skill_copies_directory(tmp_path):
    src = tmp_path / "src" / "cool-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: Cool\n---\n")
    (src / "helper.py").write_text("# helper\n")

    dest_root = tmp_path / "dest"
    installed = install_skill(src, dest_root)

    assert installed == dest_root / "cool-skill"
    assert (installed / "SKILL.md").exists()
    assert (installed / "helper.py").exists()


def test_install_skill_creates_dest_root(tmp_path):
    src = tmp_path / "src" / "new-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: New\n---\n")

    dest_root = tmp_path / "deep" / "nested" / "skills"
    install_skill(src, dest_root)
    assert dest_root.exists()


def test_install_skill_raises_if_no_skill_md(tmp_path):
    src = tmp_path / "not-a-skill"
    src.mkdir()

    with pytest.raises(ValueError, match=r"missing SKILL\.md"):
        install_skill(src, tmp_path / "dest")


def test_install_skill_raises_if_already_exists(tmp_path):
    src = tmp_path / "src" / "dupe-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: Dupe\n---\n")

    dest_root = tmp_path / "dest"
    install_skill(src, dest_root)

    with pytest.raises(FileExistsError):
        install_skill(src, dest_root)


def test_cli_list_shows_skill(tmp_path, monkeypatch):
    skill = tmp_path / "awesome-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\ndescription: Does awesome things\n---\n")

    original = cli_mod._all_roots

    def patched_roots(_settings):
        return [tmp_path]

    monkeypatch.setattr(cli_mod, "_all_roots", patched_roots)
    result = runner.invoke(app, ["list"])
    cli_mod._all_roots = original

    assert result.exit_code == 0
    assert "awesome-skill" in result.output
    assert "Does awesome things" in result.output
    assert str(skill) in result.output


def test_cli_list_no_skills_message(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_mod, "_all_roots", lambda _s: [tmp_path])
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No skills found" in result.output


def test_cli_install_workspace(tmp_path, monkeypatch):
    src = tmp_path / "src" / "my-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: Test\n---\n")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", str(src)])

    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "skills" / "my-skill" / "SKILL.md").exists()
    assert "my-skill" in result.output
    assert "workspace" in result.output


def test_cli_install_user(tmp_path, monkeypatch):
    src = tmp_path / "src" / "global-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: Global\n---\n")

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    result = runner.invoke(app, ["install", str(src), "--user"])

    assert result.exit_code == 0
    assert (fake_home / ".agents" / "skills" / "global-skill" / "SKILL.md").exists()
    assert "user" in result.output


def test_cli_install_nonexistent_source(tmp_path):
    result = runner.invoke(app, ["install", str(tmp_path / "ghost")])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_cli_install_not_a_skill(tmp_path):
    src = tmp_path / "src" / "bad"
    src.mkdir(parents=True)

    result = runner.invoke(app, ["install", str(src)])
    assert result.exit_code == 1
    assert "SKILL.md" in result.output


def test_cli_install_already_exists(tmp_path, monkeypatch):
    src = tmp_path / "src" / "dup-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: Dup\n---\n")

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install", str(src)])
    result = runner.invoke(app, ["install", str(src)])

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_cli_install_force_overwrites(tmp_path, monkeypatch):
    src = tmp_path / "src" / "force-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\ndescription: Force\n---\n")

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install", str(src)])

    (src / "SKILL.md").write_text("---\ndescription: Updated\n---\n")
    result = runner.invoke(app, ["install", str(src), "--force"])

    assert result.exit_code == 0
    installed = tmp_path / ".agents" / "skills" / "force-skill" / "SKILL.md"
    assert "Updated" in installed.read_text()
