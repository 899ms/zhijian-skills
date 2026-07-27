#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


EXCLUDED_PARTS = {".git", ".agents", "node_modules", "__pycache__"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.suffix != ".pyc"
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)
    }


def compare_manifests(
    expected: dict[str, str], actual: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    expected_paths = set(expected)
    actual_paths = set(actual)
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    changed = sorted(
        path for path in expected_paths & actual_paths if expected[path] != actual[path]
    )
    return missing, extra, changed


def bounded_output(value: str, limit: int = 4000) -> str:
    return value[-limit:]


def render(result: dict[str, Any], json_only: bool) -> None:
    if json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"Status: {result['status']}")
    print(f"Phase: {result['phase']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    if result.get("file_count") is not None:
        print(f"Files verified: {result['file_count']}")
    for field in ("missing", "extra", "changed"):
        for path in result.get(field, []):
            print(f"[{field}] {path}")


def fail(
    result: dict[str, Any],
    *,
    phase: str,
    error: str,
    json_only: bool,
) -> int:
    result.update({"status": "fail", "phase": phase, "error": error})
    render(result, json_only)
    return 2


def resolve_install_source(raw: str | None, repo: Path) -> str:
    if raw is None:
        return str(repo)
    candidate = Path(raw).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    return raw


def resolve_node(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    candidate = shutil.which("node")
    if not candidate:
        return None
    try:
        resolved = subprocess.run(
            [candidate, "-p", "process.execPath"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return candidate
    executable = resolved.stdout.strip()
    if resolved.returncode == 0 and executable and Path(executable).is_file():
        return executable
    return candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install one Skill into an isolated workspace with copy mode and "
            "fail unless every payload file matches byte-for-byte."
        )
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument(
        "--install-source",
        help="Local path or remote skills source; defaults to --repo.",
    )
    parser.add_argument("--node", help="Node executable; defaults to PATH lookup.")
    parser.add_argument("--cli", type=Path, help="skills CLI entrypoint.")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    source_skill = repo / "skills" / args.skill
    cli = (
        args.cli.expanduser().resolve()
        if args.cli
        else repo / "node_modules" / "skills" / "bin" / "cli.mjs"
    )
    node = resolve_node(args.node)
    result: dict[str, Any] = {
        "status": "fail",
        "phase": "preflight",
        "skill": args.skill,
        "install_source": resolve_install_source(args.install_source, repo),
        "missing": [],
        "extra": [],
        "changed": [],
    }

    if not repo.is_dir():
        return fail(result, phase="preflight", error="repository directory is missing", json_only=args.json)
    if not (source_skill / "SKILL.md").is_file():
        return fail(result, phase="preflight", error="Skill payload is missing SKILL.md", json_only=args.json)
    if not node:
        return fail(result, phase="preflight", error="Node executable is unavailable", json_only=args.json)
    if not cli.is_file():
        return fail(result, phase="preflight", error="skills CLI entrypoint is missing", json_only=args.json)

    expected = package_manifest(source_skill)
    with tempfile.TemporaryDirectory(prefix="skill-isolated-install-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        isolated_home = root / "home"
        workspace.mkdir()
        isolated_home.mkdir()
        environment = {
            "HOME": str(isolated_home),
            "PATH": os.environ.get("PATH", ""),
            "NO_COLOR": "1",
            "CI": "1",
        }
        command = [
            node,
            str(cli),
            "add",
            result["install_source"],
            "--skill",
            args.skill,
            "--agent",
            "codex",
            "--copy",
            "--yes",
        ]
        try:
            installed = subprocess.run(
                command,
                cwd=workspace,
                env=environment,
                text=True,
                capture_output=True,
                timeout=args.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["install_exception"] = str(exc)
            return fail(
                result,
                phase="install",
                error="isolated install command could not complete",
                json_only=args.json,
            )

        result["install_returncode"] = installed.returncode
        result["install_stdout"] = bounded_output(installed.stdout)
        result["install_stderr"] = bounded_output(installed.stderr)
        if installed.returncode != 0:
            return fail(
                result,
                phase="install",
                error="isolated install command failed",
                json_only=args.json,
            )

        installed_skill = workspace / ".agents" / "skills" / args.skill
        if not installed_skill.is_dir():
            return fail(
                result,
                phase="materialization",
                error="install command succeeded without materializing the Skill",
                json_only=args.json,
            )

        actual = package_manifest(installed_skill)
        missing, extra, changed = compare_manifests(expected, actual)
        result.update(
            {
                "phase": "compare",
                "missing": missing,
                "extra": extra,
                "changed": changed,
                "file_count": len(expected),
            }
        )
        if missing or extra or changed:
            return fail(
                result,
                phase="compare",
                error="installed payload differs from the canonical Skill",
                json_only=args.json,
            )

    result.update({"status": "pass", "phase": "compare", "error": None})
    render(result, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
