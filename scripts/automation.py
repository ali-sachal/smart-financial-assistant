"""Safe repository cleanup, Git delivery, and Vercel deployment automation."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "secrets.json", "credentials.json"}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks", ".keystore"}
GENERATED_CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CONVENTIONAL_SUBJECT = re.compile(r"^(feat|fix|docs|test|refactor|perf|build|ci|chore)(\([a-z0-9_.-]+\))?!?: .+")


class AutomationError(RuntimeError):
    pass


@dataclass
class CleanupResult:
    directories: int = 0
    files: int = 0


def clean_python_cache(root: Path = ROOT, *, dry_run: bool = False) -> CleanupResult:
    root = root.resolve()
    result = CleanupResult()
    cache_dirs = [
        path for path in root.rglob("*")
        if path.is_dir() and path.name in GENERATED_CACHE_NAMES and ".git" not in path.parts
    ]
    for path in cache_dirs:
        if not path.resolve().is_relative_to(root):
            raise AutomationError(f"Refusing to delete outside repository: {path}")
        result.directories += 1
        if not dry_run:
            shutil.rmtree(path)
    for suffix in ("*.pyc", "*.pyo"):
        for path in root.rglob(suffix):
            if ".git" in path.parts or any(parent.name == "__pycache__" for parent in path.parents):
                continue
            if not path.resolve().is_relative_to(root):
                raise AutomationError(f"Refusing to delete outside repository: {path}")
            result.files += 1
            if not dry_run:
                path.unlink()
    return result


def run_command(
    args: Sequence[str],
    *,
    root: Path = ROOT,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    completed = subprocess.run(
        list(args), cwd=root, env=merged_env, text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
    )
    if check and completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise AutomationError(f"Command failed ({' '.join(args)}): {detail}")
    return completed


def require_git_repository(root: Path = ROOT) -> None:
    completed = run_command(["git", "rev-parse", "--show-toplevel"], root=root, check=False)
    if completed.returncode:
        raise AutomationError("This directory is not a Git repository; initialize or clone it first")
    if Path(completed.stdout.strip()).resolve() != root.resolve():
        raise AutomationError("Run automation from the repository root")


def require_current_branch(branch: str, root: Path = ROOT) -> None:
    current = run_command(["git", "branch", "--show-current"], root=root).stdout.strip()
    if current != branch:
        raise AutomationError(f"Current branch is {current!r}; expected {branch!r}")


def validate_project(root: Path = ROOT) -> None:
    compile_script = (
        "from pathlib import Path; "
        "files=[*Path('app').rglob('*.py'),*Path('ai').rglob('*.py'),*Path('scripts').rglob('*.py')]; "
        "[compile(p.read_text(encoding='utf-8'),str(p),'exec') for p in files]; "
        "print(f'compiled {len(files)} files')"
    )
    env = {"PYTHONDONTWRITEBYTECODE": "1"}
    run_command([sys.executable, "-c", compile_script], root=root, env=env)
    run_command([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], root=root, env=env)


def _safe_staged_summary(root: Path = ROOT, limit: int = 12_000) -> str:
    names = run_command(["git", "diff", "--cached", "--name-status"], root=root).stdout
    stat = run_command(["git", "diff", "--cached", "--stat"], root=root).stdout
    safe_lines = []
    for line in names.splitlines():
        path = line.split("\t")[-1]
        path_obj = Path(path)
        lower_parts = {part.lower() for part in path_obj.parts}
        if (
            path_obj.name.lower() in SENSITIVE_NAMES
            or path_obj.suffix.lower() in SENSITIVE_SUFFIXES
            or "secrets" in lower_parts
            or "credentials" in lower_parts
        ):
            safe_lines.append(f"{line.split(chr(9))[0]}\t[REDACTED SENSITIVE FILE]")
        else:
            safe_lines.append(line)
    summary = "Changed files:\n" + "\n".join(safe_lines) + "\n\nStatistics:\n" + stat
    return summary[:limit]


def fallback_commit_message(summary: str) -> str:
    paths = [line.split("\t")[-1] for line in summary.splitlines() if "\t" in line]
    if paths and all(path.startswith(("docs/", "README")) for path in paths):
        return "docs: update project documentation"
    if paths and all("test" in path.lower() for path in paths):
        return "test: update automated test coverage"
    return "chore: update application platform"


def generate_commit_message(summary: str) -> str:
    try:
        from ai.llms.gateway import llm_gateway

        result = llm_gateway.chat([
            {
                "role": "system",
                "content": (
                    "Write one Conventional Commit message for the supplied file-name and diff-stat summary. "
                    "Use a <=72 character subject. You may add a short body after a blank line. "
                    "Return only the commit message. Do not claim details not present in the summary."
                ),
            },
            {"role": "user", "content": summary},
        ])
        message = str(result.content or "").strip().strip("`")
        subject = message.splitlines()[0] if message else ""
        if not CONVENTIONAL_SUBJECT.match(subject) or len(subject) > 72:
            raise ValueError("AI returned an invalid Conventional Commit subject")
        return message
    except Exception as exc:
        print(f"AI commit message unavailable ({type(exc).__name__}); using safe fallback", file=sys.stderr)
        return fallback_commit_message(summary)


def git_delivery(branch: str, remote: str = "origin", *, root: Path = ROOT, dry_run: bool = False) -> str:
    clean_python_cache(root, dry_run=dry_run)
    require_git_repository(root)
    require_current_branch(branch, root)
    validate_project(root)
    clean_python_cache(root, dry_run=dry_run)
    if dry_run:
        return f"DRY RUN: would stage, create an AI commit, and push {remote}/{branch}"
    run_command(["git", "add", "-A"], root=root)
    if not run_command(["git", "diff", "--cached", "--quiet"], root=root, check=False).returncode:
        return "No changes to commit"
    summary = _safe_staged_summary(root)
    message = generate_commit_message(summary)
    run_command(["git", "commit", "-m", message], root=root)
    try:
        run_command(["git", "push", remote, branch], root=root)
    except AutomationError as exc:
        raise AutomationError(
            f"Commit was created locally but push failed. Resolve the remote issue and run: git push {remote} {branch}. {exc}"
        ) from exc
    return message


def _require_vercel(root: Path) -> None:
    if shutil.which("vercel") is None:
        raise AutomationError("Vercel CLI is not installed or not available on PATH")
    if not (root / ".vercel" / "project.json").is_file():
        raise AutomationError("Vercel project is not linked; run 'vercel link' explicitly first")


def vercel_delivery(*, production: bool = False, root: Path = ROOT, dry_run: bool = False) -> str:
    clean_python_cache(root, dry_run=dry_run)
    require_git_repository(root)
    _require_vercel(root)
    validate_project(root)
    clean_python_cache(root, dry_run=dry_run)
    command = ["vercel", "deploy"] + (["--prod"] if production else [])
    if dry_run:
        return "DRY RUN: would stage all changes and run " + " ".join(command)
    run_command(["git", "add", "-A"], root=root)
    deployment = run_command(command, root=root)
    url = deployment.stdout.strip().splitlines()[-1] if deployment.stdout.strip() else ""
    if not url:
        raise AutomationError("Vercel completed without returning a deployment URL")
    return url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    clean = subparsers.add_parser("clean", help="Remove Python cache artifacts")
    clean.add_argument("--dry-run", action="store_true")
    git = subparsers.add_parser("git", help="Validate, commit, and push the current branch")
    git.add_argument("--branch", required=True)
    git.add_argument("--remote", default="origin")
    git.add_argument("--dry-run", action="store_true")
    vercel = subparsers.add_parser("vercel", help="Validate, stage, and deploy with Vercel")
    vercel.add_argument("--prod", action="store_true")
    vercel.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.mode == "clean":
            result = clean_python_cache(dry_run=args.dry_run)
            print(f"Python cache cleanup: {result.directories} directories, {result.files} files")
        elif args.mode == "git":
            print(git_delivery(args.branch, args.remote, dry_run=args.dry_run))
        else:
            print(vercel_delivery(production=args.prod, dry_run=args.dry_run))
        return 0
    except AutomationError as exc:
        print(f"automation error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
