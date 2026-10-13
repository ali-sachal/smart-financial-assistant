import subprocess
from pathlib import Path

import pytest

from scripts import automation


def git(root: Path, *args: str):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def init_repo(root: Path):
    git(root, "init")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test User")
    (root / "README.md").write_text("initial", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "chore: initial")


def test_cache_cleanup_and_dry_run(tmp_path):
    cache = tmp_path / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    artifact = cache / "module.pyc"
    artifact.write_bytes(b"cache")
    result = automation.clean_python_cache(tmp_path, dry_run=True)
    assert result.directories == 1 and artifact.exists()
    automation.clean_python_cache(tmp_path)
    assert not cache.exists()


def test_git_mode_rejects_missing_repository(tmp_path):
    with pytest.raises(automation.AutomationError, match="not a Git repository"):
        automation.git_delivery("main", root=tmp_path, dry_run=True)


def test_git_mode_rejects_branch_mismatch(tmp_path):
    init_repo(tmp_path)
    branch = git(tmp_path, "branch", "--show-current").stdout.strip()
    with pytest.raises(automation.AutomationError, match="expected"):
        automation.git_delivery(branch + "-other", root=tmp_path, dry_run=True)


def test_git_mode_commits_and_pushes_with_fake_ai(monkeypatch, tmp_path):
    repository = tmp_path / "repository"
    remote = tmp_path / "remote.git"
    repository.mkdir()
    init_repo(repository)
    git(tmp_path, "init", "--bare", str(remote))
    git(repository, "remote", "add", "origin", str(remote))
    branch = git(repository, "branch", "--show-current").stdout.strip()
    (repository / "README.md").write_text("updated", encoding="utf-8")
    monkeypatch.setattr(automation, "validate_project", lambda root: None)
    monkeypatch.setattr(automation, "generate_commit_message", lambda summary: "chore: test delivery")

    assert automation.git_delivery(branch, root=repository) == "chore: test delivery"
    remote_head = git(repository, "ls-remote", "origin", f"refs/heads/{branch}").stdout
    assert f"refs/heads/{branch}" in remote_head


def test_vercel_dry_run_does_not_stage(monkeypatch, tmp_path):
    init_repo(tmp_path)
    (tmp_path / "changed.txt").write_text("change", encoding="utf-8")
    monkeypatch.setattr(automation, "_require_vercel", lambda root: None)
    monkeypatch.setattr(automation, "validate_project", lambda root: None)
    result = automation.vercel_delivery(root=tmp_path, dry_run=True)
    assert result.startswith("DRY RUN")
    assert git(tmp_path, "diff", "--cached", "--name-only").stdout.strip() == ""


def test_vercel_validation_rejects_missing_project_link(monkeypatch, tmp_path):
    monkeypatch.setattr(automation.shutil, "which", lambda command: "vercel" if command == "vercel" else None)
    with pytest.raises(automation.AutomationError, match="not linked"):
        automation._require_vercel(tmp_path)


def test_staged_summary_redacts_sensitive_file_names(tmp_path):
    init_repo(tmp_path)
    (tmp_path / ".env").write_text("SECRET=do-not-send", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')", encoding="utf-8")
    git(tmp_path, "add", "-A")
    summary = automation._safe_staged_summary(tmp_path)
    assert "do-not-send" not in summary
    assert "[REDACTED SENSITIVE FILE]" in summary
    assert "app.py" in summary
