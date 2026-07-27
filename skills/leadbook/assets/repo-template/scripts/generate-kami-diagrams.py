#!/usr/bin/env python3
"""Generate Kami-style SVG information diagrams from VISUAL_PLAN.md.

This generator follows the current Kami diagram model: a diagram is an inline
SVG primitive, not a framed card. The SVG itself carries only the structure;
the book provides the surrounding text and caption.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


BRAND = "#1B365D"
TINT = "#EEF2F7"
PARCHMENT = "#f5f4ed"
IVORY = "#faf9f5"
NEAR_BLACK = "#141413"
OLIVE = "#504e49"
STONE = "#6b6a64"
BORDER = "#e8e6dc"
MIST = "#eae9e1"
WHITE = "#ffffff"

WIDTH = 960
HEIGHT = 320
FONT = "'TsangerJinKai02', 'Source Han Serif SC', 'Noto Serif CJK SC', 'Songti SC', serif"
MONO = "'JetBrains Mono', 'SF Mono', Consolas, monospace"

TYPE_ALIASES = {
    "flowchart": "flowchart",
    "state-machine": "flowchart",
    "layer-stack": "layer-stack",
    "tree": "layer-stack",
    "quadrant": "quadrant",
    "timeline": "timeline",
    "swimlane": "swimlane",
    "waterfall": "waterfall",
    "funnel": "funnel",
    "bar-chart": "bar-chart",
}


def parse_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        if any("待填写" in value for value in (row.get("Reader Problem", ""), row.get("Visual Purpose", ""))):
            continue
        rows.append(row)
    return rows


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip())
    return value or "diagram"


def wrap_chars(text: str, max_chars: int, max_lines: int) -> list[str]:
    text = " ".join(text.strip().split())
    if not text:
        return []

    lines: list[str] = []
    current = ""
    for ch in text:
        if len(current) >= max_chars:
            lines.append(current)
            current = ch
        else:
            current += ch
    if current:
        lines.append(current)

    if len(lines) <= max_lines:
        return lines

    kept = lines[:max_lines]
    kept[-1] = kept[-1][: max(1, max_chars - 1)] + "…"
    return kept


def text_block(
    text: str,
    x: float,
    y: float,
    *,
    size: int = 18,
    width: int = 8,
    fill: str = NEAR_BLACK,
    weight: int | None = None,
    max_lines: int = 2,
    anchor: str = "middle",
    mono: bool = False,
) -> str:
    family = MONO if mono else FONT
    weight_attr = f' font-weight="{weight}"' if weight else ""
    lines = wrap_chars(text, width, max_lines)
    parts = [
        f'<text x="{x:.0f}" y="{y:.0f}" fill="{fill}" font-size="{size}" '
        f'font-family="{family}" text-anchor="{anchor}"{weight_attr}>'
    ]
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else str(size + 6)
        parts.append(f'<tspan x="{x:.0f}" dy="{dy}">{esc(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def chevron(x: int, y: int, direction: str = "right", color: str = OLIVE) -> str:
    if direction == "right":
        path = f"M {x - 6},{y - 5} L {x},{y} L {x - 6},{y + 5}"
    elif direction == "down":
        path = f"M {x - 5},{y - 6} L {x},{y} L {x + 5},{y - 6}"
    else:
        path = f"M {x + 6},{y - 5} L {x},{y} L {x + 6},{y + 5}"
    return f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'


def node(
    x: int,
    y: int,
    w: int,
    h: int,
    label: str,
    *,
    index: int | None = None,
    focal: bool = False,
    muted: bool = False,
) -> str:
    fill = TINT if focal else (MIST if muted else WHITE)
    stroke = BRAND if focal else (STONE if muted else NEAR_BLACK)
    label_fill = BRAND if focal else STONE
    number = f"{index:02d}" if index is not None else ""
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PARCHMENT}"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>',
    ]
    if number:
        parts.append(
            f'<text x="{x + 18}" y="{y + 22}" fill="{label_fill}" font-size="8" '
            f'font-family="{MONO}" letter-spacing="0.12em">{number}</text>'
        )
    parts.append(text_block(label, x + w / 2, y + h / 2 + 8, size=18, width=7, weight=600, max_lines=2))
    return "\n".join(parts)


def flow_nodes(labels: list[str]) -> str:
    labels = labels[:4]
    x_positions = [4, 264, 524, 784]
    y = 112
    w = 172
    h = 72
    parts: list[str] = []
    for index, label in enumerate(labels):
        x = x_positions[index]
        if index:
            x1 = x_positions[index - 1] + w
            x2 = x - 8
            ay = y + h // 2
            color = BRAND if index == len(labels) - 1 else OLIVE
            parts.append(f'<line x1="{x1}" y1="{ay}" x2="{x2}" y2="{ay}" stroke="{color}" stroke-width="1.4"/>')
            parts.append(chevron(x2, ay, "right", color))
        parts.append(node(x, y, w, h, label, index=index + 1, focal=index == len(labels) - 1))
    return "\n".join(parts)


def signal_cards(labels: list[str]) -> str:
    labels = labels[:4]
    x_positions = [4, 264, 524, 784]
    parts: list[str] = []
    for index, label in enumerate(labels):
        parts.append(node(x_positions[index], 104, 172, 104, label, index=index + 1, focal=index == len(labels) - 1))
    return "\n".join(parts)


def timeline(labels: list[str]) -> str:
    labels = labels[:4]
    x_positions = [80, 346, 614, 880]
    axis_y = 160
    parts = [
        f'<line x1="4" y1="{axis_y}" x2="956" y2="{axis_y}" stroke="#b8b7b0" stroke-width="1.4"/>',
        chevron(956, axis_y, "right", "#b8b7b0"),
    ]
    for index, label in enumerate(labels):
        x = x_positions[index]
        above = index % 2 == 0
        card_y = 52 if above else 192
        line_start = card_y + 64 if above else axis_y
        line_end = axis_y if above else card_y
        color = BRAND if index == len(labels) - 1 else STONE
        fill = TINT if index == len(labels) - 1 else WHITE
        parts.append(f'<line x1="{x}" y1="{line_start}" x2="{x}" y2="{line_end}" stroke="{color}" stroke-width="1" stroke-dasharray="4,3"/>')
        parts.append(f'<circle cx="{x}" cy="{axis_y}" r="6" fill="{color}" stroke="{PARCHMENT}" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x - 72}" y="{card_y}" width="144" height="64" rx="6" fill="{fill}" stroke="{color}" stroke-width="1"/>')
        day = [1, 10, 20, 30][index]
        parts.append(
            f'<text x="{x}" y="{card_y + 20}" fill="{color}" font-size="8" font-family="{MONO}" '
            f'text-anchor="middle" letter-spacing="0.12em">DAY {day:02d}</text>'
        )
        parts.append(text_block(label, x, card_y + 44, size=18, width=6, weight=600, max_lines=1))
    return "\n".join(parts)


def layer_stack(labels: list[str]) -> str:
    labels = labels[:5]
    y0 = 28
    parts: list[str] = []
    for index, label in enumerate(labels):
        y = y0 + index * 52
        focal = index == 2
        fill = TINT if focal else [IVORY, PARCHMENT, PARCHMENT, MIST, "#e2e1d8"][min(index, 4)]
        stroke = BRAND if focal else [NEAR_BLACK, OLIVE, OLIVE, STONE, "#b8b7b0"][min(index, 4)]
        parts.append(f'<rect x="4" y="{y}" width="952" height="44" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        parts.append(
            f'<text x="36" y="{y + 27}" fill="{BRAND if focal else STONE}" font-size="8" '
            f'font-family="{MONO}" letter-spacing="0.15em">{index + 1:02d}</text>'
        )
        parts.append(text_block(label, 116, y + 29, size=18, width=16, weight=600, max_lines=1, anchor="start"))
    return "\n".join(parts)


def quadrant(labels: list[str]) -> str:
    labels = (labels + ["客户明确", "代价明显", "结果可描述", "路径可信"])[:4]
    positions = [(28, 52), (516, 52), (28, 184), (516, 184)]
    parts = [
        f'<rect x="4" y="32" width="952" height="256" fill="none" stroke="{BORDER}" stroke-width="1"/>',
        f'<line x1="480" y1="32" x2="480" y2="288" stroke="{BORDER}" stroke-width="1"/>',
        f'<line x1="4" y1="160" x2="956" y2="160" stroke="{BORDER}" stroke-width="1"/>',
    ]
    for index, (x, y) in enumerate(positions):
        focal = index == 3
        parts.append(f'<rect x="{x}" y="{y}" width="416" height="76" rx="6" fill="{TINT if focal else WHITE}" stroke="{BRAND if focal else NEAR_BLACK}" stroke-width="1"/>')
        parts.append(text_block(labels[index], x + 208, y + 46, size=20, width=10, weight=600, max_lines=2))
    return "\n".join(parts)


def swimlane(labels: list[str]) -> str:
    labels = labels[:4]
    lane_y = [32, 120, 208]
    parts = [
        f'<rect x="4" y="{lane_y[0]}" width="952" height="88" fill="rgba(20,20,19,0.02)"/>',
        f'<rect x="4" y="{lane_y[1]}" width="952" height="88" fill="{TINT}" opacity="0.45"/>',
        f'<rect x="4" y="{lane_y[2]}" width="952" height="88" fill="rgba(20,20,19,0.02)"/>',
        f'<line x1="4" y1="{lane_y[1]}" x2="956" y2="{lane_y[1]}" stroke="{BRAND}" stroke-width="0.8" stroke-dasharray="4,3"/>',
        f'<line x1="4" y1="{lane_y[2]}" x2="956" y2="{lane_y[2]}" stroke="{BORDER}" stroke-width="0.8" stroke-dasharray="4,3"/>',
    ]
    coords = [(28, 56), (286, 144), (544, 144), (802, 232)]
    for index, label in enumerate(labels):
        x, y = coords[index]
        if index:
            px, py = coords[index - 1]
            x1 = px + 136
            y1 = py + 32
            x2 = x - 8
            y2 = y + 32
            color = BRAND if index in {1, 2} else OLIVE
            parts.append(f'<polyline points="{x1},{y1} {x1 + 32},{y1} {x1 + 32},{y2} {x2},{y2}" fill="none" stroke="{color}" stroke-width="1.3"/>')
            parts.append(chevron(x2, y2, "right", color))
        parts.append(node(x, y, 132, 56, label, index=index + 1, focal=index in {1, 2}, muted=index == 3))
    return "\n".join(parts)


def waterfall(labels: list[str]) -> str:
    labels = labels[:4]
    x_positions = [4, 264, 524, 784]
    heights = [44, 72, 100, 128]
    base = 260
    parts: list[str] = []
    for index, label in enumerate(labels):
        h = heights[index]
        x = x_positions[index]
        y = base - h
        focal = index == len(labels) - 1
        fill = TINT if focal else [WHITE, IVORY, MIST, TINT][index]
        stroke = BRAND if focal else [NEAR_BLACK, OLIVE, STONE, BRAND][index]
        parts.append(f'<rect x="{x}" y="{y}" width="172" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        parts.append(text_block(label, x + 86, y + h / 2 + 6, size=17, width=8, weight=600, max_lines=1))
        if index < len(labels) - 1:
            x1 = x + 172
            x2 = x_positions[index + 1] - 8
            y_mid = y + 8
            parts.append(f'<line x1="{x1}" y1="{y_mid}" x2="{x2}" y2="{y_mid}" stroke="{OLIVE}" stroke-width="1.2"/>')
            parts.append(chevron(x2, y_mid, "right", OLIVE))
    parts.append(f'<line x1="4" y1="{base}" x2="956" y2="{base}" stroke="#b8b7b0" stroke-width="1"/>')
    return "\n".join(parts)


def labels_for(row: dict[str, str]) -> list[str]:
    source = row.get("Caption") or row.get("Visual Purpose") or row.get("Reader Problem") or row.get("ID", "")
    labels = [
        part.strip()
        for part in source.replace("，", "/").replace("、", "/").replace("→", "/").split("/")
        if part.strip()
    ]
    fallback = [
        value.strip()
        for value in (row.get("Reader Problem", ""), row.get("Visual Purpose", ""), row.get("Caption", ""))
        if value.strip()
    ]
    return labels if len(labels) >= 3 else fallback


def body_for(row: dict[str, str]) -> str:
    labels = labels_for(row)
    requested_type = row.get("Type", "flowchart")
    if requested_type not in TYPE_ALIASES:
        raise ValueError(f"Unsupported diagram type: {requested_type}")
    visual_type = TYPE_ALIASES[requested_type]
    if visual_type == "layer-stack":
        return layer_stack(labels)
    if visual_type == "quadrant":
        return quadrant(labels)
    if visual_type == "timeline":
        return timeline(labels)
    if visual_type == "swimlane":
        return swimlane(labels)
    if visual_type == "waterfall":
        return waterfall(labels)
    if visual_type == "funnel":
        return signal_cards(labels)
    if visual_type == "bar-chart":
        return signal_cards(labels)
    if visual_type == "flowchart":
        return flow_nodes(labels)
    raise ValueError(f"Unsupported diagram type: {requested_type}")


def svg_for(row: dict[str, str]) -> str:
    title = row.get("Visual Purpose") or row.get("Caption") or row.get("ID", "Diagram")
    pattern_id = f"dots-{slug(row.get('ID', 'diagram'))}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{esc(title)}">
<defs>
  <pattern id="{pattern_id}" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="0.9" fill="rgba(20,20,19,0.08)" />
  </pattern>
</defs>
<rect width="100%" height="100%" fill="{PARCHMENT}" />
<rect width="100%" height="100%" fill="url(#{pattern_id})" opacity="0.45" />
{body_for(row)}
</svg>
"""


def should_generate(row: dict[str, str]) -> bool:
    visual_type = row.get("Type", "")
    if visual_type in {"cover-visual", "section-visual"}:
        return False
    required = row.get("Required", "").lower()
    status = row.get("Status", "").lower()
    return required in {"yes", "true", "必须"} and status != "rejected"


def safe_output_path(root: Path, raw_output: str) -> Path:
    candidate = (root / raw_output).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError(f"Diagram output escapes project root: {raw_output}")
    if candidate.suffix.lower() != ".svg":
        raise ValueError(f"Diagram output must be .svg: {raw_output}")
    return candidate


def mark_diagram_output(root: Path) -> None:
    state_path = root / "book-state.yaml"
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")
    updated = re.sub(
        r"(?m)^(\s+kami_diagrams:)\s*[^\n]+$",
        r"\1 true",
        text,
        count=1,
    )
    if updated != text:
        state_path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Leadbook repo root")
    parser.add_argument("--visual-plan", default="VISUAL_PLAN.md")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rows = parse_table(root / args.visual_plan)
    generated = 0
    for row in rows:
        if not should_generate(row):
            continue
        output = row.get("Output Path") or f'assets/diagrams/{row.get("ID", "diagram")}.svg'
        try:
            output_path = safe_output_path(root, output)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            svg = svg_for(row)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        output_path.write_text(svg, encoding="utf-8")
        print(output_path)
        generated += 1

    if generated == 0:
        print("No required Kami diagrams found.")
    else:
        mark_diagram_output(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
