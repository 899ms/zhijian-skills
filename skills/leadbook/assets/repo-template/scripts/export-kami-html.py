#!/usr/bin/env python3
"""Convert dist/book.md into a Kami-style long document HTML."""

from __future__ import annotations

import argparse
import html
import re
import shutil
from pathlib import Path


DEFAULT_KAMI = Path.home() / ".agents" / "skills" / "kami"
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
MD_IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
DIAGRAM_TOKEN_RE = re.compile(r"\{\{\s*kami-diagram:([a-zA-Z0-9_.-]+)\s*\}\}")
SECTION_IMAGE_TOKEN_RE = re.compile(r"\{\{\s*section-image:([a-zA-Z0-9_.-]+)\s*\}\}")
STATE_RE = re.compile(r"^([a-z_]+):\s*\"?([^\"\n]+)\"?\s*$")


def infer_root(markdown_path: Path) -> Path:
    resolved = markdown_path.resolve()
    if resolved.parent.name == "dist":
        return resolved.parent.parent
    return Path.cwd().resolve()


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[end + 4 :].lstrip()
    return text


def read_state(root: Path) -> dict[str, str]:
    state_path = root / "book-state.yaml"
    if not state_path.exists():
        return {}
    values: dict[str, str] = {}
    for line in state_path.read_text(encoding="utf-8").splitlines():
        if line[:1].isspace():
            continue
        match = STATE_RE.match(line.strip())
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def read_visual_captions(root: Path) -> dict[str, str]:
    path = root / "VISUAL_PLAN.md"
    if not path.exists():
        return {}
    table_lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(table_lines) < 3:
        return {}
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    captions: dict[str, str] = {}
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        visual_id = row.get("ID", "")
        caption = row.get("Caption", "")
        if visual_id and caption and "待填写" not in caption:
            captions[visual_id] = caption
    return captions


def extract_title(markdown: str, state: dict[str, str]) -> str:
    if state.get("title"):
        return state["title"]
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Leadbook"


def inline_md(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r'<span class="hl">\1</span>', text)
    return text


def figure_html(src: str, caption: str = "") -> str:
    safe_src = html.escape(src, quote=True)
    safe_caption = inline_md(caption) if caption else ""
    caption_html = f"<figcaption>{safe_caption}</figcaption>" if safe_caption else ""
    return f'<figure class="leadbook-figure"><img src="{safe_src}" alt="{html.escape(caption, quote=True)}">{caption_html}</figure>'


def visual_token_html(kind: str, visual_id: str, captions: dict[str, str]) -> str:
    if kind == "diagram":
        src = f"assets/diagrams/{visual_id}.svg"
    else:
        suffix = "" if Path(visual_id).suffix else ".png"
        src = f"assets/images/{visual_id}{suffix}"
    return figure_html(src, captions.get(visual_id, visual_id.replace("-", " ")))


def table_to_html(rows: list[str]) -> str:
    parsed: list[list[str]] = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        parsed.append(cells)
    if len(parsed) >= 2 and all(set(cell) <= {"-", ":", " "} for cell in parsed[1]):
        header = parsed[0]
        body_rows = parsed[2:]
    else:
        header = []
        body_rows = parsed

    parts = ['<table class="leadbook-table">']
    if header:
        parts.append("<thead><tr>")
        for cell in header:
            parts.append(f"<th>{inline_md(cell)}</th>")
        parts.append("</tr></thead>")
    parts.append("<tbody>")
    for row in body_rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{inline_md(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def markdown_to_html(markdown: str, captions: dict[str, str] | None = None) -> str:
    captions = captions or {}
    lines = strip_frontmatter(markdown).splitlines()
    body: list[str] = []
    in_ul = False
    in_ol = False
    in_code = False
    in_section = False
    code_lines: list[str] = []
    first_h1 = True
    i = 0

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            body.append("</ul>")
            in_ul = False
        if in_ol:
            body.append("</ol>")
            in_ol = False

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                body.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                close_lists()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not line.strip():
            close_lists()
            i += 1
            continue

        if DIAGRAM_TOKEN_RE.fullmatch(line.strip()):
            close_lists()
            visual_id = DIAGRAM_TOKEN_RE.fullmatch(line.strip()).group(1)
            body.append(visual_token_html("diagram", visual_id, captions))
            i += 1
            continue
        if SECTION_IMAGE_TOKEN_RE.fullmatch(line.strip()):
            close_lists()
            visual_id = SECTION_IMAGE_TOKEN_RE.fullmatch(line.strip()).group(1)
            body.append(visual_token_html("image", visual_id, captions))
            i += 1
            continue
        image_match = MD_IMAGE_RE.match(line.strip())
        if image_match:
            close_lists()
            alt, src = image_match.groups()
            body.append(figure_html(src, alt))
            i += 1
            continue
        if is_table_line(line):
            close_lists()
            table_rows: list[str] = []
            while i < len(lines) and is_table_line(lines[i].rstrip()):
                table_rows.append(lines[i].rstrip())
                i += 1
            body.append(table_to_html(table_rows))
            continue
        if line.startswith("# "):
            close_lists()
            if first_h1:
                first_h1 = False
                i += 1
                continue
            if in_section:
                body.append("</section>")
            in_section = True
            body.append('<section class="chapter">')
            body.append(f"<h1>{inline_md(line[2:].strip())}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            close_lists()
            body.append(f"<h2>{inline_md(line[3:].strip())}</h2>")
            i += 1
            continue
        if line.startswith("### "):
            close_lists()
            body.append(f"<h3>{inline_md(line[4:].strip())}</h3>")
            i += 1
            continue
        if line.startswith("> "):
            close_lists()
            body.append(f"<blockquote>{inline_md(line[2:].strip())}</blockquote>")
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_ul:
                close_lists()
                body.append("<ul>")
                in_ul = True
            item = re.sub(r"^\s*[-*]\s+", "", line)
            body.append(f"<li>{inline_md(item)}</li>")
            i += 1
            continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            if not in_ol:
                close_lists()
                body.append("<ol>")
                in_ol = True
            item = re.sub(r"^\s*\d+[.)]\s+", "", line)
            body.append(f"<li>{inline_md(item)}</li>")
            i += 1
            continue

        close_lists()
        body.append(f"<p>{inline_md(line)}</p>")
        i += 1

    close_lists()
    if in_code:
        body.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    if in_section:
        body.append("</section>")
    return "\n".join(body)


def load_template(kami_skill: Path) -> str:
    path = kami_skill / "assets" / "templates" / "long-doc.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>{{文档标题}}</title>
<meta name="author" content="{{作者}}"><meta name="description" content="{{摘要}}">
<meta name="keywords" content="{{关键词}}"><style>body{font-family:serif;background:#f5f4ed;color:#141413;line-height:1.55;margin:42px auto;max-width:820px}h1{border-left:4px solid #1B365D;padding-left:12px}h2{margin-top:32px}.hl{color:#1B365D}</style></head><body>{{BODY}}</body></html>"""


def copy_tree_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            copy_tree_if_exists(item, target)
        else:
            shutil.copy2(item, target)


def copy_assets(root: Path, output_path: Path, kami_skill: Path) -> None:
    asset_root = output_path.parent / "assets"
    copy_tree_if_exists(kami_skill / "assets" / "fonts", asset_root / "fonts")
    copy_tree_if_exists(root / "assets" / "fonts", asset_root / "fonts")
    copy_tree_if_exists(root / "assets" / "diagrams", asset_root / "diagrams")
    copy_tree_if_exists(root / "assets" / "images", asset_root / "images")


def build_cover(title: str, state: dict[str, str], root: Path) -> str:
    subtitle = state.get("subtitle") or "一份独立、高质量、可公开传播的商业短书"
    author = state.get("author") or "Kami"
    created = state.get("created") or ""
    cover_img = root / "assets" / "images" / "cover-visual.png"
    image_html = ""
    if cover_img.exists():
        image_html = '<div class="leadbook-cover-art"><img src="assets/images/cover-visual.png" alt=""></div>'
    return f"""
<section class="cover leadbook-cover">
  <div class="leadbook-cover-copy">
    <div class="cover-eyebrow">LEADBOOK</div>
    <div class="cover-title">{html.escape(title)}</div>
    <div class="cover-sub">{html.escape(subtitle)}</div>
  </div>
  {image_html}
  <div class="cover-meta">
    <strong>{html.escape(author)}</strong><br>
    V1.0 {html.escape(created)}
  </div>
</section>
"""


def build_toc(markdown: str) -> str:
    heads = [line[2:].strip() for line in strip_frontmatter(markdown).splitlines() if line.startswith("# ")]
    heads = heads[1:] if len(heads) > 1 else heads
    rows = ['<section class="toc"><h2>目录</h2>']
    for index, head in enumerate(heads, 1):
        rows.append(
            f'<div class="toc-item"><span class="toc-num">{index:02d}</span>'
            f'<span class="toc-title">{html.escape(head)}</span><span class="toc-page"></span></div>'
        )
    rows.append("</section>")
    return "\n".join(rows)


def inject_css(template: str) -> str:
    extra = """
.leadbook-cover{position:relative;overflow:hidden}
.leadbook-cover-copy{max-width:70%;position:relative;z-index:2}
.leadbook-cover-art{position:absolute;right:28px;bottom:76px;width:48%;max-height:46%;z-index:1}
.leadbook-cover-art img{width:100%;height:auto;display:block}
.leadbook-figure{break-inside:avoid;margin:28px 0;text-align:left;width:100%}
.leadbook-figure img{display:block;width:100%;max-width:100%;height:auto;border-radius:0}
.leadbook-figure figcaption{margin-top:9px;font-size:.84em;color:#5b6470;text-align:left}
.leadbook-table{width:100%;border-collapse:collapse;margin:20px 0;break-inside:avoid;font-size:.92em}
.leadbook-table th,.leadbook-table td{border-top:1px solid rgba(27,54,93,.18);padding:8px 10px;vertical-align:top}
.leadbook-table th{color:#1B365D;text-align:left;font-weight:600}
"""
    if "</style>" in template:
        return template.replace("</style>", extra + "\n</style>", 1)
    if "</head>" in template:
        return template.replace("</head>", f"<style>{extra}</style></head>", 1)
    return template + f"<style>{extra}</style>"


def mark_html_output(root: Path) -> None:
    state_path = root / "book-state.yaml"
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")
    updated = re.sub(r"(?m)^(\s+kami_html:)\s*[^\n]+$", r"\1 true", text, count=1)
    for key, value in {
        "status": "draft",
        "target": "draft",
        "review_ready": "false",
        "publish_ready": "false",
        "final_report_state": "draft",
        "kami_pdf": "false",
        "pdf_visual_audit": "false",
    }.items():
        updated = re.sub(rf"(?m)^(\s*{key}:)\s*.*$", rf"\1 {value}", updated, count=1)
    if updated != text:
        state_path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", nargs="?", default="dist/book.md")
    parser.add_argument("output", nargs="?", default="dist/book.html")
    parser.add_argument("--kami-skill", default=str(DEFAULT_KAMI))
    parser.add_argument("--author", default=None)
    parser.add_argument("--keywords", default="leadbook,商业短书,白皮书,方法论")
    args = parser.parse_args()

    markdown_path = Path(args.markdown)
    output_path = Path(args.output)
    root = infer_root(markdown_path)
    markdown = markdown_path.read_text(encoding="utf-8")
    state = read_state(root)
    captions = read_visual_captions(root)
    title = extract_title(strip_frontmatter(markdown), state)
    author = args.author or state.get("author") or "Kami"
    description = re.sub(r"\s+", " ", strip_frontmatter(markdown))[:150]

    kami_skill = Path(args.kami_skill)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    copy_assets(root, output_path, kami_skill)

    template = load_template(kami_skill)
    content = build_cover(title, state, root) + build_toc(markdown) + markdown_to_html(markdown, captions)
    if "<body>" in template and "</body>" in template:
        template = re.sub(r"<body>.*?</body>", "<body>\n" + content + "\n</body>", template, flags=re.S)
    else:
        template = template.replace("{{BODY}}", content)

    replacements = {
        "{{文档标题}}": html.escape(title),
        "{{作者}}": html.escape(author),
        "{{摘要}}": html.escape(description),
        "{{关键词}}": html.escape(args.keywords),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    template = PLACEHOLDER_RE.sub("", template)
    template = inject_css(template)

    output_path.write_text(template, encoding="utf-8")
    mark_html_output(root)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
