#!/usr/bin/env python3
"""Create a leadbook project from the bundled repo template."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_VOICE_ANCHORS = {
    "strategy-consultant": "Peter Drucker + Clayton Christensen",
    "operator-playbook": "Alex Hormozi + Ramit Sethi",
    "research-analyst": "Mary Meeker + Ben Thompson",
    "product-architect": "Jeff Bezos + Marty Cagan",
    "austrian-economics": "Friedrich Hayek + Ludwig von Mises + Israel Kirzner",
    "teacher-coach": "Richard Feynman + Sal Khan",
}
PROJECT_MARKER = ".leadbook-project.json"


def replace_tokens(path: Path, values: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        replacement = value
        if path.suffix in {".yaml", ".yml"}:
            replacement = json.dumps(value, ensure_ascii=False)[1:-1]
        text = text.replace("{{" + key + "}}", replacement)
    path.write_text(text, encoding="utf-8")


def protected_target(target: Path, skill_dir: Path) -> bool:
    protected = {
        Path(target.anchor).resolve(),
        Path.home().resolve(),
        Path.cwd().resolve(),
        skill_dir.resolve(),
        skill_dir.parent.resolve(),
    }
    return target.resolve() in protected


def prepare_target(target: Path, skill_dir: Path, force: bool) -> None:
    if protected_target(target, skill_dir):
        raise SystemExit(f"Refusing protected target: {target}")
    if not target.exists() or not any(target.iterdir()):
        return
    if not force:
        raise SystemExit(f"Target is not empty: {target}. Use --force only for an existing Leadbook project.")
    marker = target / PROJECT_MARKER
    if not marker.is_file():
        raise SystemExit(
            f"Refusing to replace an unmarked directory: {target}. "
            f"Expected {PROJECT_MARKER}."
        )


def install_staging(staging: Path, target: Path) -> None:
    if not target.exists():
        staging.rename(target)
        return
    if not any(target.iterdir()):
        target.rmdir()
        staging.rename(target)
        return

    backup = target.parent / f".{target.name}.leadbook-backup-{os.getpid()}"
    if backup.exists():
        raise SystemExit(f"Refusing existing backup path: {backup}")
    target.rename(backup)
    try:
        staging.rename(target)
    except Exception:
        backup.rename(target)
        raise
    shutil.rmtree(backup)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a leadbook repo.")
    parser.add_argument("target", help="Target project directory")
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument("--subtitle", default="", help="Book subtitle")
    parser.add_argument("--content-profile", default=None, help="Content profile")
    parser.add_argument("--profile", default=None, help="Backward-compatible alias for --content-profile")
    parser.add_argument("--voice-profile", default="operator-playbook", help="Expert voice profile")
    parser.add_argument("--voice-anchor", default=None, help="Celebrity anchor for the voice profile")
    parser.add_argument("--author", default="Kami", help="Author name")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    template_dir = skill_dir / "assets" / "repo-template"
    target = Path(args.target).expanduser().resolve()

    prepare_target(target, skill_dir, args.force)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".{target.name}.leadbook-staging-{os.getpid()}"
    if staging.exists():
        raise SystemExit(f"Refusing existing staging path: {staging}")
    try:
        shutil.copytree(template_dir, staging)

        today = dt.date.today().isoformat()
        content_profile = args.content_profile or args.profile or "methodology-book"
        voice_anchor = args.voice_anchor or DEFAULT_VOICE_ANCHORS.get(args.voice_profile, args.voice_profile)
        values = {
            "TITLE": args.title,
            "SUBTITLE": args.subtitle or "一份独立、高质量、可公开传播的商业短书",
            "CONTENT_PROFILE": content_profile,
            "VOICE_PROFILE": args.voice_profile,
            "VOICE_ANCHOR": voice_anchor,
            "PROFILE": content_profile,
            "AUTHOR": args.author,
            "DATE": today,
        }

        for path in staging.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".yaml", ".py", ".html"}:
                replace_tokens(path, values)

        (staging / PROJECT_MARKER).write_text(
            json.dumps(
                {
                    "format": "leadbook-project",
                    "version": 1,
                    "created": today,
                    "title": args.title,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(staging / "scripts" / "sync-summary.py"), "--root", str(staging)],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(staging / "scripts" / "leadbook-stage.py"),
                "--root",
                str(staging),
                "mark",
                "scaffold",
                "--note",
                "Project scaffold created",
            ],
            check=True,
        )
        install_staging(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
