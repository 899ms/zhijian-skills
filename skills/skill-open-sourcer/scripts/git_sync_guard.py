#!/usr/bin/env python3
"""Fail closed when a canonical checkout is based on stale remote history."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MARKER_NAME = "zhijian-needs-sync.json"
HOOK_SENTINEL = "# ZHIJIAN_SKILLS_NEEDS_SYNC_GUARD"
CANONICAL_REMOTE_SUFFIXES = (
    "github.com/zjp1997720/zhijian-skills",
    "github.com:zjp1997720/zhijian-skills",
)


class SyncGuardError(RuntimeError):
    pass


def git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=check,
    )


def git_path(repo: Path, *args: str) -> Path:
    value = git(repo, "rev-parse", *args).stdout.strip()
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def marker_path(repo: Path) -> Path:
    return git_path(repo, "--git-common-dir") / MARKER_NAME


def read_marker(repo: Path) -> dict[str, Any] | None:
    path = marker_path(repo)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncGuardError(f"sync.marker_invalid: {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("status") not in {
        "release-in-progress",
        "needs-sync",
    }:
        raise SyncGuardError(f"sync.marker_invalid: {path}")
    return payload


def ensure_checkout_ready(repo: Path) -> None:
    marker = read_marker(repo)
    if marker is not None:
        raise SyncGuardError(
            "sync.needs_sync: checkout is frozen until it is reconciled with "
            f"origin/main ({marker_path(repo)})"
        )


def origin_url(repo: Path) -> str:
    result = git(repo, "remote", "get-url", "origin", check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise SyncGuardError("sync.origin_missing: canonical origin is unavailable")
    return result.stdout.strip()


def verify_canonical_origin(repo: Path) -> str:
    value = origin_url(repo)
    normalized = value.removesuffix(".git").rstrip("/")
    if os.environ.get("ZHIJIAN_ALLOW_TEST_REMOTE") == "1" and (
        value.startswith("file://") or Path(value).is_absolute()
    ):
        return value
    if not any(normalized.endswith(suffix) for suffix in CANONICAL_REMOTE_SUFFIXES):
        raise SyncGuardError(f"sync.origin_mismatch: {value}")
    return value


def remote_head(repo: Path, *, remote: str = "origin", branch: str = "main") -> str:
    ref = f"refs/heads/{branch}"
    result = git(repo, "ls-remote", "--heads", remote, ref, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or "ls-remote failed"
        raise SyncGuardError(f"sync.remote_unavailable: {detail}")
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    matches = [row[0] for row in rows if len(row) == 2 and row[1] == ref]
    if len(matches) != 1 or len(matches[0]) != 40:
        raise SyncGuardError(f"sync.remote_ambiguous: expected one {ref}")
    return matches[0]


def commit_guard_path(repo: Path) -> Path:
    return git_path(repo, "--git-path", "hooks/pre-commit")


def commit_guard_content() -> str:
    return f"""#!/bin/sh
{HOOK_SENTINEL}
git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null) || exit 1
if [ -f "$git_common_dir/{MARKER_NAME}" ]; then
  echo "Commit blocked: this checkout is marked needs-sync." >&2
  echo "Reconcile it with origin/main before creating new commits." >&2
  exit 1
fi
exit 0
"""


def install_commit_guard(repo: Path) -> Path:
    path = commit_guard_path(repo)
    expected = commit_guard_content()
    if path.exists():
        current = path.read_text(encoding="utf-8", errors="replace")
        if current != expected:
            raise SyncGuardError(
                f"sync.hook_conflict: refusing to replace existing pre-commit hook {path}"
            )
        path.chmod(path.stat().st_mode | 0o111)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8")
    path.chmod(0o755)
    return path


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def mark_needs_sync(
    repo: Path,
    *,
    status: str,
    base_remote_sha: str,
    integration_repo: Path,
    plan_id: str,
    observed_remote_head: str | None = None,
) -> Path:
    repo = repo.resolve()
    verify_canonical_origin(repo)
    install_commit_guard(repo)
    payload = {
        "schema_version": "1.0.0",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_remote_sha": base_remote_sha,
        "local_head": git(repo, "rev-parse", "HEAD").stdout.strip(),
        "integration_repo": str(integration_repo.resolve()),
        "plan_id": plan_id,
        "observed_remote_head": observed_remote_head,
    }
    path = marker_path(repo)
    atomic_write_json(path, payload)
    return path


def clear_marker(repo: Path, *, expected_remote_sha: str) -> None:
    repo = repo.resolve()
    path = marker_path(repo)
    if not path.is_file():
        return
    if git(repo, "status", "--porcelain").stdout.strip():
        raise SyncGuardError("sync.clear_dirty: checkout must be clean")
    local_head = git(repo, "rev-parse", "HEAD").stdout.strip()
    actual_remote = remote_head(repo)
    if local_head != expected_remote_sha or actual_remote != expected_remote_sha:
        raise SyncGuardError("sync.clear_mismatch: local and remote main must match")
    path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--repo", required=True)
    clear = subparsers.add_parser("clear")
    clear.add_argument("--repo", required=True)
    clear.add_argument("--expected-remote-sha", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo = Path(args.repo).expanduser().resolve()
    try:
        verify_canonical_origin(repo)
        if args.command == "check":
            ensure_checkout_ready(repo)
            print(json.dumps({"status": "ready", "remote_head": remote_head(repo)}))
        else:
            clear_marker(repo, expected_remote_sha=args.expected_remote_sha)
            print(json.dumps({"status": "cleared"}))
    except (OSError, subprocess.CalledProcessError, SyncGuardError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
