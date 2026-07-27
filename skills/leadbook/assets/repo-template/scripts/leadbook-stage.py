#!/usr/bin/env python3
"""Persist resumable Leadbook phase checkpoints with lightweight completion guards."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


PHASES = [
    "scaffold",
    "brief",
    "research",
    "outline",
    "writing",
    "build",
    "visual-qa",
    "review-ready",
    "publish-ready",
]
URL_RE = re.compile(r"https?://[^\s<>|)\]`\"]+")


def default_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "current_phase": "scaffold",
        "phases": {
            phase: {
                "status": "completed" if phase == "scaffold" else "pending",
                "updated_at": None,
                "note": "",
            }
            for phase in PHASES
        },
    }


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return default_state()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("phases"), dict):
        raise SystemExit(f"Invalid Leadbook checkpoint file: {path}")
    return data


def save_state(path: Path, state: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def text_has_content(path: Path, minimum: int = 120) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return len(text.strip()) >= minimum and "待填写" not in text


def receipt_passed(root: Path, target: str) -> bool:
    path = root / "dist" / "qa" / "gates" / f"{target}.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return data.get("target") == target and data.get("passed") is True


def validate_phase(root: Path, phase: str) -> list[str]:
    missing: list[str] = []
    if phase == "brief":
        for name in ("BOOK_BRIEF.md", "READER_PROFILE.md", "POSITIONING.md", "src/INTRODUCTION.md"):
            if not text_has_content(root / name):
                missing.append(name)
    elif phase == "research":
        files = (
            "SOURCE_MAP.md",
            "CLAIM_LEDGER.md",
            "CASE_LIBRARY.md",
            "BEHAVIOR_LEDGER.md",
            "TRANSACTION_LEDGER.md",
            "bibliography.md",
        )
        combined = ""
        for name in files:
            path = root / name
            if not text_has_content(path, 80):
                missing.append(name)
            elif path.is_file():
                combined += path.read_text(encoding="utf-8", errors="ignore") + "\n"
        if len(set(URL_RE.findall(combined))) < 6:
            missing.append("at least 6 unique public URLs")
    elif phase == "outline":
        path = root / "OUTLINE.md"
        if not path.is_file() or len(re.findall(r"(?m)^##\s+", path.read_text(encoding="utf-8"))) < 3:
            missing.append("OUTLINE.md with at least 3 chapters")
    elif phase == "writing":
        chapters = sorted((root / "src").glob("chapter-*/README.md"))
        written = [
            path
            for path in chapters
            if "leadbook-template: chapter" not in path.read_text(encoding="utf-8", errors="ignore")
        ]
        if len(written) < 3:
            missing.append("at least 3 completed chapter files")
    elif phase == "build":
        for name in ("dist/book.md", "dist/book.html", "dist/book.pdf"):
            path = root / name
            if not path.is_file() or path.stat().st_size < 100:
                missing.append(name)
    elif phase == "visual-qa":
        path = root / "dist" / "qa" / "pdf-visual-audit.md"
        if not path.is_file() or "audit_state: passed" not in path.read_text(encoding="utf-8"):
            missing.append("dist/qa/pdf-visual-audit.md with audit_state: passed")
    elif phase in {"review-ready", "publish-ready"} and not receipt_passed(root, phase):
        missing.append(f"passing {phase} gate receipt")
    return missing


def next_phase(state: dict[str, object]) -> str | None:
    phase_state = state["phases"]
    for phase in PHASES:
        if phase_state[phase]["status"] != "completed":
            return phase
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("next")
    mark = subparsers.add_parser("mark")
    mark.add_argument("phase", choices=PHASES)
    mark.add_argument("--status", choices=("in-progress", "completed", "blocked"), default="completed")
    mark.add_argument("--note", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    path = root / ".leadbook-run.json"
    state = load_state(path)
    if args.command == "status":
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    if args.command == "next":
        print(next_phase(state) or "complete")
        return 0

    if args.status == "completed":
        phase_index = PHASES.index(args.phase)
        incomplete_prior = [
            phase
            for phase in PHASES[:phase_index]
            if state["phases"][phase]["status"] != "completed"
        ]
        if incomplete_prior:
            raise SystemExit("Cannot complete phase before: " + ", ".join(incomplete_prior))
        missing = validate_phase(root, args.phase)
        if missing:
            raise SystemExit(f"Cannot complete {args.phase}; missing: " + ", ".join(missing))

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    state["phases"][args.phase] = {"status": args.status, "updated_at": now, "note": args.note}
    state["current_phase"] = next_phase(state) or "complete"
    save_state(path, state)
    print(json.dumps(state["phases"][args.phase], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
