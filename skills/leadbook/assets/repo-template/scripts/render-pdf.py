#!/usr/bin/env python3
"""Render Leadbook HTML to PDF with a local WeasyPrint-first pipeline."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def chrome_binary() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ]
    return next((str(c) for c in candidates if c and Path(c).exists()), None)


def configure_weasyprint_runtime() -> None:
    """Make Homebrew native libs discoverable before importing WeasyPrint."""
    os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "leadbook-fontconfig-cache"))

    if sys.platform != "darwin":
        return

    for prefix in (Path("/opt/homebrew"), Path("/usr/local")):
        brew_lib = prefix / "lib"
        if not (brew_lib / "libgobject-2.0.dylib").exists():
            continue

        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        paths = [path for path in existing.split(":") if path]
        brew_lib_str = str(brew_lib)
        if brew_lib_str not in paths:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join([brew_lib_str, *paths])
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", nargs="?", default="dist/book.html")
    parser.add_argument("pdf", nargs="?", default="dist/book.pdf")
    args = parser.parse_args()

    html_path = Path(args.html).resolve()
    pdf_path = Path(args.pdf).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    weasy_error: Exception | None = None
    try:
        configure_weasyprint_runtime()
        from weasyprint import HTML

        HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))
        mark_pdf_output(html_path, pdf_path)
        print(pdf_path)
        return 0
    except (ImportError, OSError) as exc:
        weasy_error = exc

    chrome = chrome_binary()
    if not chrome:
        detail = f" ({type(weasy_error).__name__}: {weasy_error})" if weasy_error else ""
        raise SystemExit("WeasyPrint and Chrome fallback are unavailable" + detail)

    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--allow-file-access-from-files",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        check=True,
    )
    mark_pdf_output(html_path, pdf_path)
    print(pdf_path)
    return 0


def mark_pdf_output(html_path: Path, pdf_path: Path) -> None:
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        return
    root = html_path.parent.parent if html_path.parent.name == "dist" else html_path.parent
    state_path = root / "book-state.yaml"
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")
    updated = re.sub(r"(?m)^(\s+kami_pdf:)\s*[^\n]+$", r"\1 true", text, count=1)
    for key, value in {
        "status": "draft",
        "target": "draft",
        "review_ready": "false",
        "publish_ready": "false",
        "final_report_state": "draft",
        "pdf_visual_audit": "false",
    }.items():
        updated = re.sub(rf"(?m)^(\s*{key}:)\s*.*$", rf"\1 {value}", updated, count=1)
    if updated != text:
        state_path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
