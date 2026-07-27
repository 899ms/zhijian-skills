#!/usr/bin/env python3
"""Export the leadbook chapters into dist/book.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TEMPLATE_MARKERS = ("<!-- leadbook-template: chapter -->", "<!-- leadbook-template: introduction -->")


def summary_paths(summary: Path) -> list[Path]:
    paths: list[Path] = []
    for line in summary.read_text(encoding="utf-8").splitlines():
        match = LINK_RE.search(line)
        if not match:
            continue
        href = match.group(1)
        if "://" in href or href.startswith("#"):
            continue
        paths.append((summary.parent / href).resolve())
    return paths


def first_heading(path: Path) -> str:
    if not path.exists():
        return "Leadbook"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Leadbook"


def bibliography_block(path: Path) -> str:
    if not path.exists():
        return ""
    text = HTML_COMMENT_RE.sub("", path.read_text(encoding="utf-8")).strip()
    if not text:
        return ""
    lines = text.splitlines()
    visible = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
    if not visible:
        return ""
    if lines and lines[0].startswith("#"):
        lines[0] = "## 参考资料"
    else:
        lines = ["## 参考资料", ""] + lines
    return "\n".join(lines).strip()


def reader_content(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if any(marker in text for marker in TEMPLATE_MARKERS):
        return ""
    return text


def mark_markdown_output(root: Path) -> None:
    state_path = root / "book-state.yaml"
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")
    updated = re.sub(
        r"(?m)^(outputs:\s*\n(?:^[ \t].*\n)*?^[ \t]+markdown:)\s*[^\n]+$",
        r"\1 true",
        text,
        count=1,
    )
    reset_values = {
        "status": "draft",
        "target": "draft",
        "review_ready": "false",
        "publish_ready": "false",
        "final_report_state": "draft",
        "kami_html": "false",
        "kami_pdf": "false",
        "pdf_visual_audit": "false",
    }
    for key, value in reset_values.items():
        updated = re.sub(
            rf"(?m)^(\s*{key}:)\s*.*$",
            rf"\1 {value}",
            updated,
            count=1,
        )
    if updated != text:
        state_path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Leadbook repo root")
    parser.add_argument("--output", default="dist/book.md")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    summary = root / "src" / "SUMMARY.md"
    if not summary.exists():
        raise SystemExit("Missing src/SUMMARY.md. Run scripts/sync-summary.py first.")

    title = first_heading(root / "OUTLINE.md")
    dist = root / "dist"
    dist.mkdir(exist_ok=True)

    chunks = [
        "---",
        f'title: "{title}"',
        f'source: "{root.name}"',
        "---",
        "",
        f"# {title}",
        "",
    ]

    introduction = reader_content(root / "src" / "INTRODUCTION.md")
    if introduction:
        chunks.extend([introduction, ""])

    for path in summary_paths(summary):
        if not path.exists():
            raise SystemExit(f"Missing chapter file referenced by SUMMARY.md: {path}")
        text = reader_content(path)
        if not text:
            continue
        chunks.append(text)
        chunks.append("")

    refs = bibliography_block(root / "bibliography.md")
    if refs:
        chunks.append(refs)
        chunks.append("")

    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks).strip() + "\n", encoding="utf-8")
    mark_markdown_output(root)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
