#!/usr/bin/env python3
"""Generate src/SUMMARY.md and chapter folders from OUTLINE.md.

Chinese headings are never used as file paths. Chapters always map to
chapter-01, chapter-02, ... in outline order.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CHAPTER_RE = re.compile(r"^(#{2})\s+(.+?)\s*$")
STATE_VALUE_RE = re.compile(r"^([a-z_]+):\s*\"?([^\"\n]+)\"?\s*$")

PROFILE_TEMPLATE_GUIDES = {
    "whitepaper": {
        "note": "这是一个 `whitepaper` 章节脚手架。先推进判断和证据链，再决定哪些动作值得给读者。不要默认写成训练手册。",
        "path": [
            "从真实背景、变化或代价切入，说明这一章为什么重要。",
            "拆清这一章要判断的核心问题、概念边界或常见误判。",
            "用事实、公开来源和案例把判断钉住。",
            "写清风险、限制和对读者的实际影响。",
            "只在必要处给出路线图或决策建议。",
        ],
        "optional": ["- 事实背景", "- 趋势判断", "- 反方证据", "- 风险边界", "- 影响清单"],
    },
    "playbook": {
        "note": "这是一个 `playbook` 章节脚手架。它允许更强的动作密度，但仍然要推进整本书判断，不能每章都像同一张 SOP。",
        "path": [
            "从一个具体场景或失败信号切入，说明读者为什么会卡住。",
            "指出常见旧做法为什么不行，别急着直接给步骤。",
            "给出这一章的核心方法、步骤或判断顺序。",
            "放入必要的模板、清单、表格或停手条件。",
            "收束到边界、失败信号和下一章要解决的问题。",
        ],
        "optional": ["- 错误清单", "- 步骤表", "- 模板块", "- 案例框", "- 停手条件"],
    },
    "methodology-book": {
        "note": "这是一个 `methodology-book` 章节脚手架。首要任务是推进整本书的主张和模型，不要把章节写成平均分配工具的工作手册。",
        "path": [
            "用一个旧理解、误判或反常识 tension 开章。",
            "界定这一章要澄清的概念、边界或系统关系。",
            "搭出模型，并解释每个部件为什么存在。",
            "用案例或反例验证模型，不让它停留在术语层。",
            "收束成行动原则、迁移条件或下一章的过渡问题。",
        ],
        "optional": ["- 概念边界", "- 系统模型", "- 反例", "- 迁移条件", "- 章节过渡段"],
    },
    "business-report": {
        "note": "这是一个 `business-report` 章节脚手架。重点是把事实、判断、推论和建议分开，不要用模板感覆盖分析感。",
        "path": [
            "明确这一章的研究问题或观察对象。",
            "先摆事实，再说明这些事实意味着什么。",
            "区分可确认信息、趋势判断和推论。",
            "补充机会地图、二阶影响或反方信号。",
            "最后收束成读者应该采取的判断动作。",
        ],
        "optional": ["- 研究问题", "- 事实表", "- 二阶影响", "- 机会地图", "- 建议边界"],
    },
    "course-manual": {
        "note": "这是一个 `course-manual` 章节脚手架。它最适合高密度练习和检查标准，但也要有连续学习路径，而不是纯作业表。",
        "path": [
            "先说明本章学习目标和学习门槛。",
            "用清楚解释和示例带读者理解核心概念。",
            "加入练习、清单或检查标准，帮助读者动手。",
            "指出常见错误和合格信号。",
            "收束到下一步练习或下一章衔接。",
        ],
        "optional": ["- 学习目标", "- 示例", "- 练习任务", "- 检查标准", "- 课后反思"],
    },
}


def parse_chapters(outline: Path) -> list[str]:
    chapters: list[str] = []
    for line in outline.read_text(encoding="utf-8").splitlines():
        match = CHAPTER_RE.match(line)
        if match:
            title = match.group(2).strip()
            if title:
                chapters.append(title)
    return chapters


def extract_short_title(title: str) -> str:
    title = re.sub(r"^Chapter\s*\d+\s*[:：]\s*", "", title, flags=re.I)
    title = re.sub(r"^第\s*\d+\s*章\s*[:：]?\s*", "", title)
    return title.strip() or title


def read_state_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line[:1].isspace():
            continue
        match = STATE_VALUE_RE.match(line.strip())
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def profile_template_guide(content_profile: str) -> dict[str, str]:
    guide = PROFILE_TEMPLATE_GUIDES.get(content_profile, PROFILE_TEMPLATE_GUIDES["methodology-book"])
    return {
        "CHAPTER_PROFILE_NOTE": guide["note"],
        "CHAPTER_PATH_GUIDE": "\n".join(f"- {item}" for item in guide["path"]),
        "CHAPTER_OPTIONAL_BLOCKS": "\n".join(guide["optional"]),
    }


def replace_template_tokens(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def read_existing_chapters(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    chapters: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.startswith("- id:"):
            chapter_id = stripped.split(":", 1)[1].strip().strip('"\'')
            current = {"id": chapter_id}
            chapters[chapter_id] = current
            continue
        if current is None:
            continue
        match = re.match(r"^([a-z_]+):\s*(.*?)\s*$", stripped)
        if match and match.group(2):
            current[match.group(1)] = match.group(2).strip().strip('"\'')
    return chapters


def meaningful_table_rows(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    header_seen = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if not header_seen:
            header_seen = True
            continue
        if any("待填写" in cell for cell in cells):
            continue
        count += 1
    return count


def chapter_metrics(chapter_dir: Path) -> tuple[int, int, int]:
    readme = chapter_dir / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if "<!-- leadbook-template: chapter -->" in text:
        words = 0
    else:
        words = len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", text))
    return words, meaningful_table_rows(chapter_dir / "refs.md"), meaningful_table_rows(chapter_dir / "cases.md")


def default_state_preamble(title: str, existing: dict[str, str]) -> str:
    return "\n".join(
        [
            f"title: {yaml_string(title)}",
            f"subtitle: {yaml_string(existing.get('subtitle', ''))}",
            f"content_profile: {yaml_string(existing.get('content_profile', existing.get('profile', 'methodology-book')))}",
            f"voice_profile: {yaml_string(existing.get('voice_profile', 'operator-playbook'))}",
            f"voice_anchor: {yaml_string(existing.get('voice_anchor', ''))}",
            f"author: {yaml_string(existing.get('author', '大鹏'))}",
            f"created: {yaml_string(existing.get('created', ''))}",
            "status: draft",
            "quality:",
            "  target: draft",
            "  review_ready: false",
            "  publish_ready: false",
            "  reference_page: false",
            "  worksheets_ready: false",
            "  distribution_pack_ready: false",
            "  final_report_state: draft",
            "completion_metrics:",
            "  evidence_coverage: 0.0",
            "  visual_coverage: 0.0",
            "  chapter_completion: 0.0",
            "  backend_language_clean: false",
            "research:",
            "  source_map: false",
            "  authority_accounts: false",
            "  authority_accounts_selected: 0",
            "  xhs_pack: false",
            "  wxmp_pack: false",
            "  wxmp_rate_limited: false",
            "  wxmp_recency_window_days: 365",
            "  behavior_seed_plan: false",
            "  behavior_pack: false",
            "  behavior_signals: 0",
            "  transaction_pack: false",
            "  transaction_signals: 0",
            "  authority_sources: 0",
            "  claim_ledger_reviewed: false",
            "  local_context_used: false",
            "outputs:",
            "  markdown: false",
            "  references: false",
            "  visual_plan: false",
            "  kami_diagrams: false",
            "  imagegen_visuals: false",
            "  kami_html: false",
            "  kami_pdf: false",
            "  pdf_visual_audit: false",
        ]
    )


def merge_state_preamble(path: Path, title: str, existing: dict[str, str]) -> str:
    if not path.exists():
        return default_state_preamble(title, existing)
    text = path.read_text(encoding="utf-8")
    preamble = re.split(r"(?m)^chapters:\s*$", text, maxsplit=1)[0].rstrip()
    title_line = f"title: {yaml_string(title)}"
    if re.search(r"(?m)^title:\s*.*$", preamble):
        preamble = re.sub(r"(?m)^title:\s*.*$", title_line, preamble, count=1)
    else:
        preamble = title_line + "\n" + preamble
    reset_values = {
        "status": "draft",
        "target": "draft",
        "review_ready": "false",
        "publish_ready": "false",
        "final_report_state": "draft",
    }
    for state_key, value in reset_values.items():
        preamble = re.sub(
            rf"(?m)^(\s*{state_key}:)\s*.*$",
            rf"\1 {value}",
            preamble,
            count=1,
        )
    for output_key in ("markdown", "kami_html", "kami_pdf", "pdf_visual_audit"):
        preamble = re.sub(
            rf"(?m)^(\s+{output_key}:)\s*.*$",
            rf"\1 false",
            preamble,
            count=1,
        )
    return preamble


def write_state(root: Path, chapters: list[str], title: str) -> None:
    state_path = root / "book-state.yaml"
    existing = read_state_values(state_path)
    existing_chapters = read_existing_chapters(state_path)
    lines = [merge_state_preamble(state_path, title, existing), "chapters:"]
    for index, chapter_title in enumerate(chapters, 1):
        chapter_id = f"chapter-{index:02d}"
        prior = existing_chapters.get(chapter_id, {})
        words, refs, cases = chapter_metrics(root / "src" / chapter_id)
        status = prior.get("status", "not-started")
        if words > 0 and status == "not-started":
            status = "draft"
        lines.extend(
            [
                f"  - id: {chapter_id}",
                f"    title: {yaml_string(extract_short_title(chapter_title))}",
                f"    status: {status}",
                f"    words: {words}",
                f"    refs: {refs}",
                f"    cases: {cases}",
                f"    reviewed: {prior.get('reviewed', 'false')}",
                f"    summary_updated: {prior.get('summary_updated', 'false')}",
            ]
        )
    state_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Leadbook repo root")
    parser.add_argument("--outline", default="OUTLINE.md")
    parser.add_argument("--write-state", action="store_true", help="Deprecated compatibility flag; state is merged by default")
    parser.add_argument("--no-write-state", action="store_true", help="Skip book-state.yaml synchronization")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    outline = root / args.outline
    if not outline.exists():
        raise SystemExit(f"Missing outline: {outline}")

    lines = outline.read_text(encoding="utf-8").splitlines()
    book_title = next((line[2:].strip() for line in lines if line.startswith("# ")), "Leadbook")
    chapters = parse_chapters(outline)
    if not chapters:
        raise SystemExit("No chapter headings found. Use '## Chapter title' in OUTLINE.md.")
    state_values = read_state_values(root / "book-state.yaml")
    content_profile = state_values.get("content_profile", state_values.get("profile", "methodology-book"))
    template_values = profile_template_guide(content_profile)
    template_values["CONTENT_PROFILE"] = content_profile

    src = root / "src"
    src.mkdir(exist_ok=True)
    introduction = src / "INTRODUCTION.md"
    if not introduction.exists():
        intro_template = root / "templates" / "introduction-template.md"
        if intro_template.exists():
            introduction.write_text(intro_template.read_text(encoding="utf-8"), encoding="utf-8")
    summary_lines = ["# Summary", ""]

    for index, chapter_title in enumerate(chapters, 1):
        chapter_id = f"chapter-{index:02d}"
        chapter_dir = src / chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)

        readme = chapter_dir / "README.md"
        if not readme.exists():
            template = root / "templates" / "chapter-template.md"
            if template.exists():
                content = template.read_text(encoding="utf-8")
                content = replace_template_tokens(content, template_values)
                content = content.replace("# Chapter X：标题", f"# Chapter {index}：{extract_short_title(chapter_title)}")
            else:
                guide = profile_template_guide(content_profile)
                content = (
                    "<!-- leadbook-template: chapter -->\n"
                    f"# Chapter {index}：{extract_short_title(chapter_title)}\n\n"
                    f"> {guide['CHAPTER_PROFILE_NOTE']}\n\n"
                    "## 本章在整本书里的任务\n\n"
                    "- 这一章要纠正的旧理解：待填写。\n"
                    "- 这一章要建立的新判断：待填写。\n"
                    "- 这一章与上一章 / 下一章的关系：待填写。\n"
                    "- 这一章更像：论证章 / 模型章 / 案例章 / 步骤章 / 边界章 / 收束章。\n\n"
                    "## 推荐展开路径\n\n"
                    f"{guide['CHAPTER_PATH_GUIDE']}\n\n"
                    "## 必须覆盖的内容检查\n\n"
                    "- 结论或判断：待填写。\n"
                    "- 读者问题：待填写。\n"
                    "- 证据或来源：待填写。\n"
                    "- 案例或反例：待填写。\n"
                    "- 行动产出：待填写。\n"
                    "- 作者判断：待填写。\n\n"
                    "## 可选块\n\n"
                    f"{guide['CHAPTER_OPTIONAL_BLOCKS']}\n\n"
                    "## 写作提醒\n\n"
                    "- 不要为了整齐重复“本章产出 / 操作方法 / 自测问题”。\n"
                    "- 能进入 `dist/worksheets/` 的填写任务，优先不占正文主结构。\n"
                    "- 让本章推进整本书，而不是单独像一张任务单。\n\n"
                    "## 本章小结\n\n待填写。\n"
                )
            readme.write_text(content, encoding="utf-8")

        for filename, title in (("refs.md", "Chapter References"), ("cases.md", "Chapter Cases")):
            path = chapter_dir / filename
            if not path.exists():
                if filename == "refs.md":
                    template = root / "templates" / "refs-template.md"
                elif filename == "cases.md":
                    template = root / "templates" / "cases-template.md"
                else:
                    template = None
                if template and template.exists():
                    path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
                else:
                    path.write_text(f"# {title}\n\n待填写。\n", encoding="utf-8")

        summary_lines.append(f"- [{extract_short_title(chapter_title)}]({chapter_id}/README.md)")

    (src / "SUMMARY.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    if not args.no_write_state:
        write_state(root, chapters, book_title)

    print(f"Synced {len(chapters)} chapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
