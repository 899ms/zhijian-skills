from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = SKILL_ROOT / "scripts" / "scaffold_leadbook.py"


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def load_script(name: str):
    path = SKILL_ROOT / "assets" / "repo-template" / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LeadbookCoreTests(unittest.TestCase):
    def scaffold(self, target: Path, *, title: str = "中小企业 AI Agent 落地") -> subprocess.CompletedProcess[str]:
        return run(
            [
                sys.executable,
                str(SCAFFOLD),
                str(target),
                "--title",
                title,
                "--content-profile",
                "playbook",
                "--voice-profile",
                "product-architect",
                "--author",
                "测试作者",
            ]
        )

    def test_scaffold_accepts_empty_target_and_syncs_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            target.mkdir()
            result = self.scaffold(target, title='测试"引号"书')
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue((target / ".leadbook-project.json").is_file())
            self.assertTrue((target / "src/chapter-01/README.md").is_file())
            self.assertIn("completion_metrics:", (target / "book-state.yaml").read_text(encoding="utf-8"))
            self.assertIn('title: "测试\\\"引号\\\"书"', (target / "book-state.yaml").read_text(encoding="utf-8"))

    def test_force_refuses_unmarked_nonempty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "important"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            result = run(
                [sys.executable, str(SCAFFOLD), str(target), "--title", "测试", "--force"]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unmarked directory", result.stderr + result.stdout)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_sync_merges_state_and_updates_outline_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            self.assertEqual(self.scaffold(target).returncode, 0)
            outline = target / "OUTLINE.md"
            outline.write_text(
                "# 三章书\n\n## Chapter 1：定义\n\n## Chapter 2：方法\n\n## Chapter 3：边界\n",
                encoding="utf-8",
            )
            state_path = target / "book-state.yaml"
            state_path.write_text(
                state_path.read_text(encoding="utf-8")
                .replace("status: draft", "status: review-ready", 1)
                .replace("  target: draft", "  target: review-ready", 1)
                .replace("  review_ready: false", "  review_ready: true", 1)
                .replace("  markdown: false", "  markdown: true"),
                encoding="utf-8",
            )
            result = run([sys.executable, "scripts/sync-summary.py"], cwd=target)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            state = state_path.read_text(encoding="utf-8")
            self.assertEqual(state.count("  - id: chapter-"), 3)
            self.assertIn("completion_metrics:", state)
            self.assertIn("research:", state)
            self.assertIn("status: draft", state)
            self.assertIn("  target: draft", state)
            self.assertIn("  review_ready: false", state)
            self.assertIn("  markdown: false", state)

    def test_empty_export_fails_draft_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            self.assertEqual(self.scaffold(target).returncode, 0)
            self.assertEqual(run([sys.executable, "scripts/export-markdown.py"], cwd=target).returncode, 0)
            checked = run(
                [sys.executable, "scripts/check-leadbook.py", "--target", "draft", "dist/book.md"],
                cwd=target,
            )
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("至少需要 1 个已写章节", checked.stdout)

    def test_wip_export_skips_templates_and_passes_one_real_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            self.assertEqual(self.scaffold(target).returncode, 0)
            (target / "src/INTRODUCTION.md").write_text(
                "读者常常从工具采购开始，却没有定义业务结果。本书先定义成功，再说明验证路径。" * 6,
                encoding="utf-8",
            )
            body = "一个可验收的试点必须写清输入、输出、责任人和停止条件。" * 30
            chapter = f"""# Chapter 1：先定义成功

## 结论与判断
{body}

## 读者场景
项目已经启动，但团队说不清最终交付什么。

## 公开证据与来源
公开项目复盘反复说明，缺少验收口径会让试点无限延期。

## 案例与反例
假设场景：团队购买工具后才寻找问题，最终无法判断是否有效。

## 行动清单
写出业务结果、基线、目标值、负责人和停止条件。

## 我的判断与边界
先定义验收，再选择工具；无法量化时也要写清可观察变化。

{{{{diagram:fig-01}}}}
"""
            (target / "src/chapter-01/README.md").write_text(chapter, encoding="utf-8")
            (target / "VISUAL_PLAN.md").write_text(
                "| ID | Chapter | Reader Problem | Visual Purpose | Type | Source | Required | Status | Output Path | Caption |\n"
                "|---|---|---|---|---|---|---|---|---|---|\n"
                "| fig-01 | chapter-01 | 看不清流程 | 展示四步 | flowchart | chapter | yes | planned | assets/diagrams/fig-01.svg | 从定义到验收 |\n",
                encoding="utf-8",
            )
            self.assertEqual(run([sys.executable, "scripts/sync-summary.py"], cwd=target).returncode, 0)
            self.assertEqual(run([sys.executable, "scripts/export-markdown.py"], cwd=target).returncode, 0)
            book = (target / "dist/book.md").read_text(encoding="utf-8")
            self.assertIn("Chapter 1", book)
            self.assertNotIn("Chapter 2", book)
            self.assertNotIn("leadbook-template", book)
            checked = run(
                [sys.executable, "scripts/check-leadbook.py", "--target", "draft", "dist/book.md"],
                cwd=target,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr or checked.stdout)
            self.assertIn("必填信息图文件不存在", checked.stdout)
            self.assertIn("markdown: true", (target / "book-state.yaml").read_text(encoding="utf-8"))

    def test_diagram_uses_plan_labels_and_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            self.assertEqual(self.scaffold(target).returncode, 0)
            header = "| ID | Chapter | Reader Problem | Visual Purpose | Type | Source | Required | Status | Output Path | Caption |\n|---|---|---|---|---|---|---|---|---|---|\n"
            row = "| fig-01 | chapter-01 | 看不清流程 | 展示四步 | flowchart | chapter | yes | planned | assets/diagrams/fig-01.svg | 需求澄清、方案设计、试点运行、验收复盘 |\n"
            (target / "VISUAL_PLAN.md").write_text(header + row, encoding="utf-8")
            generated = run([sys.executable, "scripts/generate-kami-diagrams.py"], cwd=target)
            self.assertEqual(generated.returncode, 0, generated.stderr or generated.stdout)
            svg = (target / "assets/diagrams/fig-01.svg").read_text(encoding="utf-8")
            self.assertIn("需求澄清", svg)
            self.assertIn("验收复盘", svg)
            self.assertNotIn("咨询意向", svg)

            escaped = row.replace("assets/diagrams/fig-01.svg", "../escape.svg")
            (target / "VISUAL_PLAN.md").write_text(header + escaped, encoding="utf-8")
            rejected = run([sys.executable, "scripts/generate-kami-diagrams.py"], cwd=target)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("escapes project root", rejected.stderr + rejected.stdout)
            self.assertFalse((target.parent / "escape.svg").exists())

    def test_xhs_runtime_output_redacts_token_and_raw_payload(self) -> None:
        module = load_script("xhs-research.py")
        item = module.normalize_search_result(
            "AI",
            {"id": "note-1", "xsecToken": "temporary-sensitive-value", "noteCard": {}},
        )
        public = module.public_record(item)
        serialized = json.dumps(public, ensure_ascii=False)
        self.assertNotIn("temporary-sensitive-value", serialized)
        self.assertNotIn("xsec_token", serialized)
        self.assertNotIn("raw", serialized)
        self.assertEqual(public["url"], "https://www.xiaohongshu.com/explore/note-1")
        with self.assertRaises(ValueError):
            module.validate_base_url("https://example.com", allow_remote=False)

    def test_evidence_rows_require_specific_public_urls(self) -> None:
        module = load_script("check-leadbook.py")
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "BEHAVIOR_LEDGER.md"
            header = "| ID | Source Type | URL | Signal |\n|---|---|---|---|\n"
            ledger.write_text(
                header + "| B001 | job-posting | 公开招聘平台检索入口 | 企业招聘 AI 应用岗 |\n",
                encoding="utf-8",
            )
            errors, _ = module.check_ledger_rows(
                ledger, "BEHAVIOR_LEDGER.md", 1, False, require_urls=True
            )
            self.assertTrue(any("具体 URL" in error for error in errors))

            ledger.write_text(
                header
                + "| B001 | job-posting | https://example.com/jobs/ai-operator | 企业招聘 AI 应用岗 |\n",
                encoding="utf-8",
            )
            errors, _ = module.check_ledger_rows(
                ledger, "BEHAVIOR_LEDGER.md", 1, False, require_urls=True
            )
            self.assertEqual(errors, [])

    def test_high_fact_requires_a_direct_url(self) -> None:
        module = load_script("check-leadbook.py")
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "CLAIM_LEDGER.md"
            ledger.write_text(
                "| ID | Claim | Type | Layer | Source | URL | Date | Confidence | Cross-check | Reader-facing wording | Notes |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|\n"
                "| C001 | 企业采用率上升 | fact | L1-fact | 某官方报告 | 公开报告检索 | 2026 | high | 另一报告 | 某机构在 2026 年指出采用率上升 | - |\n",
                encoding="utf-8",
            )
            errors, _ = module.check_claim_ledger(ledger, False, "review-ready")
            self.assertTrue(any("具体 URL" in error for error in errors))

    def test_gate_receipt_binds_maturity_to_current_artifacts(self) -> None:
        module = load_script("check-leadbook.py")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            self.assertEqual(self.scaffold(target).returncode, 0)
            for relative, content in {
                "dist/book.md": "# 书\n\n正文",
                "dist/book.html": "<html>正文</html>",
                "dist/book.pdf": "fake-pdf",
                "dist/qa/pdf-visual-audit.md": "audit_state: passed",
                "bibliography.md": "1. https://example.com/report/1",
            }.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            receipt = module.update_gate_state(target, "review-ready", True, [], [])
            self.assertTrue(receipt.is_file())
            state = (target / "book-state.yaml").read_text(encoding="utf-8")
            self.assertIn("status: review-ready", state)
            self.assertIn("  review_ready: true", state)
            self.assertIn("  visual_coverage: 1.0", state)
            self.assertIn("  pdf_visual_audit: true", state)
            self.assertEqual(module.verify_gate_receipt(target, "review-ready"), [])
            module.update_gate_state(target, "publish-ready", False, ["short"], [])
            state = (target / "book-state.yaml").read_text(encoding="utf-8")
            self.assertIn("status: review-ready", state)
            self.assertIn("  visual_coverage: 1.0", state)
            self.assertIn("  pdf_visual_audit: true", state)
            (target / "dist/book.md").write_text("# 书\n\n正文已经修改", encoding="utf-8")
            self.assertTrue(module.verify_gate_receipt(target, "review-ready"))
            module.update_gate_state(target, "review-ready", False, ["failed"], [])
            state = (target / "book-state.yaml").read_text(encoding="utf-8")
            self.assertIn("status: draft", state)
            self.assertIn("  review_ready: false", state)
            self.assertIn("  visual_coverage: 0.0", state)
            self.assertIn("  pdf_visual_audit: false", state)

    def test_pdf_audit_requires_all_rendered_pages_checked(self) -> None:
        checker = load_script("check-leadbook.py")
        preparer = load_script("prepare-pdf-visual-audit.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "book"
            pages = root / "dist/qa/pages"
            pages.mkdir(parents=True)
            pdf = root / "dist/book.pdf"
            pdf.write_bytes(b"not-a-real-pdf")
            images = []
            for page in (1, 2):
                image = pages / f"page-{page:02d}.png"
                image.write_bytes(b"png")
                images.append((page, image))
            audit = root / "dist/qa/pdf-visual-audit.md"
            preparer.write_audit(root, pdf, audit, ["pdftoppm", str(pdf)], images, [], None)
            errors, _ = checker.check_pdf_visual_audit(root, "review-ready")
            self.assertTrue(any("audit_state" in error for error in errors))
            text = audit.read_text(encoding="utf-8")
            text = text.replace("audit_state: pending-review", "audit_state: passed")
            text = text.replace(
                "| no | 自动渲染完成，尚未视觉检查 | pending |",
                "| yes | 无问题 | passed |",
            )
            text = text.replace("- [ ]", "- [x]")
            text = text.replace(
                "自动渲染已完成。实际视觉检查尚未完成；检查后把 audit_state 改为 passed，逐页填写 Checked、Issues、Fix Status，并勾选全部 Checklist。",
                "已逐页检查封面、目录、正文、图表和尾页，未发现未关闭问题。",
            )
            audit.write_text(text, encoding="utf-8")
            errors, _ = checker.check_pdf_visual_audit(root, "review-ready")
            self.assertEqual(errors, [])

    def test_publish_visual_audit_requires_balanced_reference_pagination(self) -> None:
        checker = load_script("check-leadbook.py")
        preparer = load_script("prepare-pdf-visual-audit.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "book"
            pages = root / "dist/qa/pages"
            pages.mkdir(parents=True)
            pdf = root / "dist/book.pdf"
            pdf.write_bytes(b"not-a-real-pdf")
            image = pages / "page-01.png"
            image.write_bytes(b"png")
            audit = root / "dist/qa/pdf-visual-audit.md"
            preparer.write_audit(
                root, pdf, audit, ["pdftoppm", str(pdf)], [(1, image)], [], None
            )
            text = audit.read_text(encoding="utf-8")
            text = text.replace("audit_state: pending-review", "audit_state: passed")
            text = text.replace(
                "| no | 自动渲染完成，尚未视觉检查 | pending |",
                "| yes | 无问题 | closed |",
            )
            text = text.replace("- [ ]", "- [x]")
            text = text.replace(
                "自动渲染已完成。实际视觉检查尚未完成；检查后把 audit_state 改为 passed，逐页填写 Checked、Issues、Fix Status，并勾选全部 Checklist。",
                "已逐页检查并关闭全部问题。",
            )
            audit.write_text(text, encoding="utf-8")
            errors, _ = checker.check_pdf_visual_audit(root, "publish-ready")
            self.assertEqual(errors, [])

            audit.write_text(
                text.replace(
                    "- [x] 参考资料分页没有单条孤项或大面积空白尾页；必要时调整参考资料排版。\n",
                    "",
                ),
                encoding="utf-8",
            )
            errors, _ = checker.check_pdf_visual_audit(root, "publish-ready")
            self.assertTrue(any("参考资料分页" in error for error in errors))

    def test_stage_checkpoint_blocks_out_of_order_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "book"
            self.assertEqual(self.scaffold(target).returncode, 0)
            self.assertTrue((target / ".leadbook-run.json").is_file())
            result = run(
                [sys.executable, "scripts/leadbook-stage.py", "mark", "writing"],
                cwd=target,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Cannot complete phase before", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
