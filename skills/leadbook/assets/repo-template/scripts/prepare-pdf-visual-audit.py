#!/usr/bin/env python3
"""Render a Leadbook PDF and create a deterministic page-by-page visual QA checklist."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import shlex
import shutil
import subprocess
from pathlib import Path


PAGE_RE = re.compile(r"page-(\d+)\.png$")


def visual_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(lines) < 3:
        return []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    found: list[str] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        visual_id = row.get("ID", "")
        required = row.get("Required", "").lower() in {"yes", "true", "必须"}
        rejected = row.get("Status", "").lower() == "rejected"
        if visual_id and required and not rejected:
            found.append(visual_id)
    return found


def page_images(path: Path) -> list[tuple[int, Path]]:
    images: list[tuple[int, Path]] = []
    for candidate in path.glob("page-*.png"):
        match = PAGE_RE.fullmatch(candidate.name)
        if match:
            images.append((int(match.group(1)), candidate))
    return sorted(images)


def render_pdf(pdf: Path, pages_dir: Path, dpi: int) -> tuple[list[str], list[tuple[int, Path]]]:
    executable = shutil.which("pdftoppm")
    if not executable:
        raise SystemExit("pdftoppm is required for PDF visual QA")
    pages_dir.mkdir(parents=True, exist_ok=True)
    for old_page in pages_dir.glob("page-*.png"):
        if old_page.is_file() and PAGE_RE.fullmatch(old_page.name):
            old_page.unlink()
    command = [executable, "-png", "-r", str(dpi), str(pdf), str(pages_dir / "page")]
    subprocess.run(command, check=True)
    images = page_images(pages_dir)
    if not images:
        raise SystemExit("pdftoppm produced no page images")
    expected = list(range(1, len(images) + 1))
    actual = [page for page, _ in images]
    if actual != expected:
        raise SystemExit(f"PDF page images are not contiguous: {actual}")
    return command, images


def create_contact_sheet(images: list[tuple[int, Path]], output: Path) -> bool:
    executable = shutil.which("montage")
    if not executable:
        return False
    command = [
        executable,
        *[str(path) for _, path in images],
        "-thumbnail",
        "300x424",
        "-tile",
        "4x",
        "-geometry",
        "+6+6",
        "-background",
        "#d9d8d0",
        str(output),
    ]
    subprocess.run(command, check=True)
    return output.is_file() and output.stat().st_size > 0


def write_audit(
    root: Path,
    pdf: Path,
    audit_path: Path,
    command: list[str],
    images: list[tuple[int, Path]],
    figures: list[str],
    contact_sheet: Path | None,
) -> None:
    generated = dt.datetime.now(dt.timezone.utc).isoformat()
    pdf_digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    relative_pdf = pdf.relative_to(root)
    command_display = [str(relative_pdf) if item == str(pdf) else item for item in command]
    lines = [
        "# PDF Visual Audit",
        "",
        "audit_state: pending-review",
        f"generated_at: {generated}",
        f"pdf_sha256: {pdf_digest}",
        f"page_count: {len(images)}",
        "expected_figures: " + (", ".join(figures) if figures else "none"),
        "",
        "## Render Command",
        "",
        f"`{shlex.join(command_display)}`",
        "",
    ]
    if contact_sheet:
        lines.extend(
            [
                f"Contact sheet: `{contact_sheet.relative_to(root)}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Page Images",
            "",
            "| Page | Image Path | Figures | Checked | Issues | Fix Status |",
            "|---|---|---|---|---|---|",
        ]
    )
    for page, image in images:
        relative_image = image.relative_to(root)
        lines.append(
            f"| {page} | {relative_image} | - | no | 自动渲染完成，尚未视觉检查 | pending |"
        )
    lines.extend(
        [
            "",
            "## Figure Coverage",
            "",
            "把每个 expected figure ID 填入其所在页面的 `Figures` 单元格；无图页面保留 `-`。",
            "",
            "## Checklist",
            "",
            "- [ ] 封面标题、副标题、作者、版本或日期不被遮挡。",
            "- [ ] 目录不出现假的页码占位符。",
            "- [ ] 每一页都已实际查看，正文、表格和分页没有截断。",
            "- [ ] 每张图与正文宽度协调，图内文字不出框、不漂移、可读。",
            "- [ ] 图表无内框大卡片、模板水印、无关备注。",
            "- [ ] caption 能独立解释图的作用。",
            "- [ ] 参考资料页和尾页可读。",
            "- [ ] 参考资料分页没有单条孤项或大面积空白尾页；必要时调整参考资料排版。",
            "- [ ] `distribution-note.md` 和 `private-domain-pack.md` 没有进入正式 PDF。",
            "",
            "## Summary",
            "",
            "自动渲染已完成。实际视觉检查尚未完成；检查后把 audit_state 改为 passed，逐页填写 Checked、Issues、Fix Status，并勾选全部 Checklist。",
            "",
        ]
    )
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Leadbook project root")
    parser.add_argument("--pdf", default="dist/book.pdf")
    parser.add_argument("--dpi", type=int, default=110)
    args = parser.parse_args()

    if args.dpi < 72 or args.dpi > 300:
        raise SystemExit("--dpi must be between 72 and 300")
    root = Path(args.root).resolve()
    pdf = (root / args.pdf).resolve()
    if root != pdf and root not in pdf.parents:
        raise SystemExit("PDF path escapes the Leadbook project")
    if not pdf.is_file() or pdf.stat().st_size < 100:
        raise SystemExit(f"Missing or empty PDF: {pdf}")

    qa_dir = root / "dist" / "qa"
    command, images = render_pdf(pdf, qa_dir / "pages", args.dpi)
    contact_sheet = qa_dir / "contact-sheet.png"
    has_contact_sheet = create_contact_sheet(images, contact_sheet)
    write_audit(
        root,
        pdf,
        qa_dir / "pdf-visual-audit.md",
        command,
        images,
        visual_ids(root / "VISUAL_PLAN.md"),
        contact_sheet if has_contact_sheet else None,
    )
    print(qa_dir / "pdf-visual-audit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
