#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path


SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", re.IGNORECASE)),
]

SECRET_NAME_PATTERN = re.compile(
    r"(?i)^(?:[a-z0-9]+[_-])*(?:api[_-]?key|secret(?:[_-]?key)?|token|password)$"
)
ASSIGNMENT_SECRET_PATTERN = re.compile(
    r"""(?imx)
    [\"']?
    (?P<key>(?:[a-z0-9]+[_-])*(?:api[_-]?key|secret(?:[_-]?key)?|token|password))
    [\"']?\s*[:=]\s*
    (?:
        (?P<quote>[\"'])(?P<quoted>[^\"'\r\n]{12,})(?P=quote)
        |
        (?P<bare>[A-Za-z0-9._~+/=${}-]{12,})(?=\s*(?:$|[,;}#]|//))
    )
    """
)
PLACEHOLDER_MARKERS = (
    "changeme",
    "dummy",
    "example",
    "placeholder",
    "redacted",
    "replace-me",
    "replace_me",
    "sample",
    "your-",
    "your_",
)

PRIVATE_PATH_PATTERNS = [
    ("mac_user_path", re.compile(r"/Users/[A-Za-z0-9._-]+/")),
    ("linux_home_path", re.compile(r"/home/[A-Za-z0-9._-]+/")),
]

SUSPICIOUS_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".DS_Store",
}

SUSPICIOUS_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".log",
}

SUSPICIOUS_DIRS: set[str] = set()
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
MAX_TEXT_BYTES = 512_000
MAX_FILE_BYTES = 2_000_000


def resolve_skill_dir(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.name == "SKILL.md":
        path = path.parent
    path = path.resolve()
    if not path.exists():
        raise SystemExit(f"Path does not exist: {path}")
    if not path.is_dir():
        raise SystemExit(f"Expected a skill directory or SKILL.md: {path}")
    if not (path / "SKILL.md").is_file():
        raise SystemExit(f"Missing SKILL.md in: {path}")
    return path


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:4096]


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            yield base / name


def add_issue(issues: list[dict], severity: str, path: Path, reason: str, detail: str = "") -> None:
    issues.append(
        {
            "severity": severity,
            "path": str(path),
            "reason": reason,
            "detail": detail[:200],
        }
    )


def is_secret_name(value: str) -> bool:
    return bool(SECRET_NAME_PATTERN.fullmatch(value.strip()))


def is_placeholder_secret(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized or normalized in {"...", "none", "null"}:
        return True
    if normalized.startswith(("${", "{{", "<")):
        return True
    if any(marker in normalized for marker in PLACEHOLDER_MARKERS):
        return True
    if re.fullmatch(r"[A-Z][A-Z0-9_]{5,}", value.strip()):
        return True
    return len(set(normalized) - {"x", "*", "_", "-"}) == 0


def is_runtime_reference(value: str) -> bool:
    normalized = value.strip()
    if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+", normalized):
        return True
    return normalized.startswith(("process.env.", "Deno.env.", "config.", "settings.", "secrets."))


def is_test_fixture_path(path: Path) -> bool:
    test_parts = {"test", "tests", "fixture", "fixtures", "__fixtures__"}
    if any(part.lower() in test_parts for part in path.parts):
        return True
    name = path.name.lower()
    return name.startswith("test_") or name.endswith(
        ("_test.py", ".test.js", ".test.jsx", ".test.ts", ".test.tsx", ".spec.js", ".spec.jsx", ".spec.ts", ".spec.tsx")
    )


def python_literal_secrets(text: str) -> list[tuple[str, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found: list[tuple[str, str]] = []

    def literal(value: ast.AST | None) -> str | None:
        return value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None

    def add(name: str | None, value_node: ast.AST | None) -> None:
        value = literal(value_node)
        if name and value is not None and len(value) >= 12 and is_secret_name(name) and not is_placeholder_secret(value):
            found.append((name, value))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    add(target.id, node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            add(node.target.id, node.value)
        elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
            add(node.target.id, node.value)
        elif isinstance(node, ast.Dict):
            for key_node, value_node in zip(node.keys, node.values):
                key = literal(key_node)
                add(key, value_node)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                add(keyword.arg, keyword.value)
    return found


def assignment_secrets(path: Path, text: str) -> list[tuple[str, str]]:
    # Test fixtures often need fake literal credentials to verify redaction and
    # precedence behavior. Provider-specific secret patterns are still scanned
    # independently for every file, including tests.
    if is_test_fixture_path(path):
        return []
    if path.suffix == ".py":
        return python_literal_secrets(text)
    found: list[tuple[str, str]] = []
    for match in ASSIGNMENT_SECRET_PATTERN.finditer(text):
        value = match.group("quoted") or match.group("bare") or ""
        if is_placeholder_secret(value) or is_runtime_reference(value):
            continue
        found.append((match.group("key"), value))
    return found


def contains_known_secret(value: str) -> bool:
    return any(pattern.search(value) for _, pattern in SECRET_PATTERNS)


def scan(root: Path) -> dict:
    issues: list[dict] = []
    files_scanned = 0

    for path in iter_files(root):
        rel = path.relative_to(root)
        files_scanned += 1

        if any(part in SUSPICIOUS_DIRS for part in rel.parts):
            add_issue(issues, "blocker", rel, "suspicious_directory")
            continue

        if path.is_symlink():
            target = path.resolve()
            if root not in target.parents and target != root:
                add_issue(issues, "blocker", rel, "symlink_escapes_package", str(target))
            continue

        if path.name in SUSPICIOUS_FILENAMES:
            add_issue(issues, "blocker", rel, "suspicious_filename")

        if path.suffix in SUSPICIOUS_SUFFIXES:
            add_issue(issues, "blocker", rel, "suspicious_file_type")

        try:
            size = path.stat().st_size
        except OSError as exc:
            add_issue(issues, "warning", rel, "unreadable_stat", str(exc))
            continue

        if size > MAX_FILE_BYTES:
            add_issue(issues, "blocker", rel, "large_file", f"{size} bytes")
            continue

        try:
            data = path.read_bytes()
        except OSError as exc:
            add_issue(issues, "warning", rel, "unreadable_file", str(exc))
            continue

        if is_binary(data):
            add_issue(issues, "warning", rel, "binary_file", f"{size} bytes")
            continue

        if len(data) > MAX_TEXT_BYTES:
            add_issue(issues, "warning", rel, "large_text_file", f"{size} bytes")
            continue

        text = data.decode("utf-8", errors="ignore")
        for label, pattern in SECRET_PATTERNS:
            matches = list(pattern.finditer(text))
            if matches:
                add_issue(
                    issues,
                    "blocker",
                    rel,
                    f"possible_secret:{label}",
                    f"<redacted:{len(matches)} match(es)>",
                )

        for key, value in assignment_secrets(path, text):
            if contains_known_secret(value):
                continue
            add_issue(
                issues,
                "blocker",
                rel,
                "possible_secret:assignment_secret",
                f"{key}=<redacted:{len(value)} chars>",
            )

        for label, pattern in PRIVATE_PATH_PATTERNS:
            match = pattern.search(text)
            if match:
                add_issue(issues, "blocker", rel, f"private_path:{label}", match.group(0))

    blockers = [issue for issue in issues if issue["severity"] == "blocker"]
    warnings = [issue for issue in issues if issue["severity"] == "warning"]
    return {
        "skill_dir": str(root),
        "files_scanned": files_scanned,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "issues": issues,
        "status": "blocked" if blockers else "clear",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a local skill for public-release blockers.")
    parser.add_argument("skill", help="Path to a skill directory or SKILL.md")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    root = resolve_skill_dir(args.skill)
    result = scan(root)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Skill: {result['skill_dir']}")
        print(f"Files scanned: {result['files_scanned']}")
        print(f"Status: {result['status']}")
        print(f"Blockers: {result['blocker_count']}")
        print(f"Warnings: {result['warning_count']}")
        for issue in result["issues"]:
            detail = f" - {issue['detail']}" if issue["detail"] else ""
            print(f"[{issue['severity']}] {issue['path']}: {issue['reason']}{detail}")

    return 2 if result["blocker_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
