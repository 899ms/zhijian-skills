from __future__ import annotations

import json
import os
import csv
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import browser_reader  # noqa: E402
import harvest_wxmp  # noqa: E402
import metaso_reader  # noqa: E402
import refresh_token_playwright  # noqa: E402
import runtime_paths  # noqa: E402


def article_url(mid: int) -> str:
    return f"https://mp.weixin.qq.com/s?__biz=test&mid={mid}&idx=1&sn=abc"


class RuntimeGuardTests(unittest.TestCase):
    def test_normalizes_http_and_rejects_non_wechat_hosts(self) -> None:
        normalized = runtime_paths.normalize_wechat_url(article_url(1).replace("https://", "http://"))
        self.assertTrue(normalized.startswith("https://mp.weixin.qq.com/s?"))
        with self.assertRaises(ValueError):
            runtime_paths.normalize_wechat_url("https://mp.weixin.qq.com.evil.example/s?id=1")
        with self.assertRaises(ValueError):
            runtime_paths.normalize_wechat_url("https://mp.weixin.qq.com/cgi-bin/home")

    def test_canonical_url_strips_tracking_and_requires_identity(self) -> None:
        value = article_url(2) + "&scene=21&utm_source=test#wechat_redirect"
        self.assertEqual(runtime_paths.normalize_wechat_url(value), article_url(2))
        with self.assertRaises(ValueError):
            runtime_paths.normalize_wechat_url("https://mp.weixin.qq.com/s?__biz=test&mid=2&idx=1")

    def test_safe_component_blocks_path_escape_and_caps_utf8_bytes(self) -> None:
        value = "../目录/" + ("很长的标题" * 80)
        result = runtime_paths.safe_component(value, max_bytes=80)
        self.assertNotIn("/", result)
        self.assertNotIn("..", result)
        self.assertLessEqual(len(result.encode("utf-8")), 80)
        self.assertRegex(result, r"\[[0-9a-f]{8}\]$")

    def test_process_lock_rejects_parallel_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "harvest.lock"
            runtime_paths.acquire_lock(lock)
            try:
                with self.assertRaises(RuntimeError):
                    runtime_paths.acquire_lock(lock)
            finally:
                runtime_paths.release_lock(lock)
            self.assertFalse(lock.exists())

    def test_login_cookie_filter_rejects_lookalike_domains(self) -> None:
        header = refresh_token_playwright.cookie_header([
            {"name": "good", "value": "1", "domain": ".mp.weixin.qq.com"},
            {"name": "bad", "value": "2", "domain": "evilweixin.qq.com"},
        ])
        self.assertEqual(header, "good=1")


class QualityGateTests(unittest.TestCase):
    def test_browser_reader_uses_generic_runtime_profile(self) -> None:
        reader = browser_reader.BrowserArticleReader()
        self.assertEqual(reader.profile, runtime_paths.DEFAULT_ARTICLE_PROFILE)

    def test_rejects_wechat_page_shell(self) -> None:
        result = metaso_reader.ReaderResult(
            url=article_url(2),
            title="Video",
            published="unknown-date",
            markdown="Video\nMini Program\nLike\n轻点两下取消赞\nWow\n轻点两下取消在看\n",
            retrieved_via="metaso",
        )
        with self.assertRaises(RuntimeError):
            metaso_reader.validate_result(result, expected_title="真实教程")

    def test_wcx_placeholder_requires_fulltext(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "placeholder.md"
            path.write_text(
                "---\ntitle: 占位文章\nlink: " + article_url(3) + "\ndigest: \"" + ("摘要" * 500) + "\"\n---\n\n*（正文尚未抓取，原链接）*",
                encoding="utf-8",
            )
            self.assertTrue(harvest_wxmp.needs_fulltext(path))

    def test_browser_verification_opens_circuit(self) -> None:
        error = "browser redirected to https://mp.weixin.qq.com/mp/wappoc_appmsgcaptcha?token=test"
        self.assertIn("risk-control", harvest_wxmp.browser_circuit_reason(error))
        self.assertEqual(harvest_wxmp.browser_circuit_reason("ordinary timeout"), "")

    def test_browser_result_keeps_inline_image_order(self) -> None:
        text = "这是教程正文。" * 60
        markdown = f"第一步 {text}\n\n![](https://mmbiz.qpic.cn/a.png)\n\n第二步 {text}"
        result = browser_reader.result_from_page_data(
            article_url(4),
            {
                "title": "手把手教程",
                "author": "测试公众号",
                "published": "2026年7月25日",
                "content": text * 2,
                "markdown": markdown,
            },
        )
        image_position = result.markdown.index("![](https://mmbiz.qpic.cn/a.png)")
        self.assertLess(result.markdown.index("第一步"), image_position)
        self.assertLess(image_position, result.markdown.index("第二步"))
        self.assertEqual(result.author, "测试公众号")
        self.assertEqual(result.published, "2026-07-25")


class IdentityAndStateTests(unittest.TestCase):
    def test_same_title_different_urls_are_not_overwritten(self) -> None:
        body = "可复用教程正文。" * 80
        with tempfile.TemporaryDirectory() as directory:
            articles = Path(directory)
            first = harvest_wxmp.ArticleRecord("同名教程", article_url(10), "2026-07-01")
            second = harvest_wxmp.ArticleRecord("同名教程", article_url(11), "2026-07-01")
            first_path = harvest_wxmp.write_article(
                first,
                metaso_reader.ReaderResult(first.url, body, first.title, first.published, "作者", "browser"),
                articles,
            )
            second_path = harvest_wxmp.write_article(
                second,
                metaso_reader.ReaderResult(second.url, body, second.title, second.published, "作者", "browser"),
                articles,
            )
            self.assertNotEqual(first_path, second_path)
            self.assertTrue(first_path.exists())
            self.assertTrue(second_path.exists())
            self.assertEqual(len(list(articles.glob("*.md"))), 2)

    def test_record_metadata_updates_from_page(self) -> None:
        body = "页面正文。" * 100
        with tempfile.TemporaryDirectory() as directory:
            record = harvest_wxmp.ArticleRecord("旧标题", article_url(12), "2026-07-20", "索引作者")
            result = metaso_reader.ReaderResult(
                record.url,
                body,
                "页面标题",
                "2026-07-21",
                "页面作者",
                "browser",
            )
            path = harvest_wxmp.write_article(record, result, Path(directory))
            self.assertEqual(record.title, "页面标题")
            self.assertEqual(record.published, "2026-07-21")
            self.assertEqual(record.author, "页面作者")
            self.assertIn("2026-07-21 页面标题", path.name)

    def test_existing_clipping_source_is_canonicalized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article.md"
            path.write_text(
                "---\nsource: \"" + article_url(13) + "&scene=21&chksm=tracking\"\n---\n\n正文\n",
                encoding="utf-8",
            )
            harvest_wxmp.normalize_article_source(path)
            self.assertIn(f'source: "{article_url(13)}"', path.read_text(encoding="utf-8"))
            self.assertNotIn("chksm", path.read_text(encoding="utf-8"))

    def test_resume_state_restores_without_account_when_unique(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_root = harvest_wxmp.DEFAULT_EXPORT_ROOT
            try:
                harvest_wxmp.DEFAULT_EXPORT_ROOT = Path(directory)
                export_dir = Path(directory) / "测试号"
                export_dir.mkdir()
                state = harvest_wxmp.BatchState(account="测试号", next_offset=60, output_dir=str(export_dir))
                harvest_wxmp.save_batch_state(state, export_dir)
                resolved_dir, resolved_state = harvest_wxmp.resolve_resume_state(None, None)
                self.assertEqual(resolved_dir, export_dir)
                self.assertEqual(resolved_state.next_offset, 60)
            finally:
                harvest_wxmp.DEFAULT_EXPORT_ROOT = original_root

    def test_cursor_coverage_uses_verified_boundary_date(self) -> None:
        self.assertTrue(harvest_wxmp.target_covered_by_cursor("2024-12-31", year=2025))
        self.assertFalse(harvest_wxmp.target_covered_by_cursor("2025-06-01", year=2025))

    def test_batch_completion_reason_is_explicit(self) -> None:
        self.assertEqual(
            harvest_wxmp.batch_completion_reason("2024-12-31", year=2025),
            "crossed_lower_bound",
        )
        self.assertEqual(
            harvest_wxmp.batch_completion_reason("", year=2025, exhausted=True),
            "remote_exhausted",
        )
        self.assertEqual(
            harvest_wxmp.batch_completion_reason("2025-07-01", year=2025),
            "in_progress",
        )

    def test_task_id_is_stable_and_fingerprint_changes_with_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            common = dict(
                account="测试号",
                year=None,
                from_date="2026-06-25",
                to_date="2026-07-25",
                title_regex="教程",
                fulltext=True,
                allow_metaso=False,
                output_dir=Path(directory),
            )
            first = harvest_wxmp.batch_config_fingerprint(**common)
            second = harvest_wxmp.batch_config_fingerprint(**{**common, "title_regex": "技巧"})
            self.assertNotEqual(first, second)
            self.assertEqual(
                harvest_wxmp.task_id_for_fingerprint(first),
                harvest_wxmp.task_id_for_fingerprint(first),
            )

    def test_index_csv_escapes_formula_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            export_dir = Path(directory)
            records = [harvest_wxmp.ArticleRecord("=1+1", article_url(30), author="@cmd")]
            harvest_wxmp.write_indexes(records, export_dir)
            with (export_dir / "index.csv").open(encoding="utf-8", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["title"], "'=1+1")
            self.assertEqual(row["author"], "'@cmd")

    def test_wcx_export_selection_uses_index_identity_not_account_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder, nickname in (("first", "甲号"), ("second", "目标号")):
                target = root / folder
                target.mkdir()
                (target / "index.json").write_text(
                    json.dumps({"account": {"nickname": nickname}, "articles": []}, ensure_ascii=False),
                    encoding="utf-8",
                )
            self.assertEqual(harvest_wxmp.locate_wcx_export_dir(root, "目标号"), root / "second")
            with self.assertRaises(RuntimeError):
                harvest_wxmp.locate_wcx_export_dir(root, "../不存在")


class CliContractTests(unittest.TestCase):
    def test_limit_above_80_fails_before_network(self) -> None:
        command = [
            sys.executable,
            str(SCRIPTS / "harvest_wxmp.py"),
            "--account",
            "测试号",
            "--limit",
            "81",
            "--no-fulltext",
        ]
        result = subprocess.run(command, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--limit must be between 1 and 80", result.stderr + result.stdout)

    def test_title_regex_filter(self) -> None:
        records = [
            harvest_wxmp.ArticleRecord("手把手教程", article_url(20)),
            harvest_wxmp.ArticleRecord("产品发布公告", article_url(21)),
        ]
        filtered = harvest_wxmp.filter_title_records(records, "教程|技巧")
        self.assertEqual([item.title for item in filtered], ["手把手教程"])

    def test_partial_result_is_not_reported_as_ok(self) -> None:
        records = [harvest_wxmp.ArticleRecord("视频教程", article_url(22), status="partial")]
        status, ok, exit_code, success, partial, failed = harvest_wxmp.classify_run_result(
            records,
            batch_mode=False,
            batch_done=False,
            rate_limited=False,
            fetch_warning=None,
        )
        self.assertEqual((status, ok, exit_code), ("partial", False, 2))
        self.assertEqual((success, partial, failed), (0, 1, 0))

    def test_batch_fetch_warning_is_not_reported_as_in_progress_ok(self) -> None:
        records = [harvest_wxmp.ArticleRecord("教程", article_url(23), status="index-only")]
        status, ok, exit_code, *_ = harvest_wxmp.classify_run_result(
            records,
            batch_mode=True,
            batch_done=False,
            rate_limited=False,
            fetch_warning="fetch failed",
        )
        self.assertEqual((status, ok, exit_code), ("partial", False, 2))

    def test_strict_iso_date_validation(self) -> None:
        self.assertEqual(str(harvest_wxmp.require_iso_date("--from-date", "2026-07-25")), "2026-07-25")
        with self.assertRaises(SystemExit):
            harvest_wxmp.require_iso_date("--from-date", "2026-7-25")

    def test_resume_before_cooldown_exits_75_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            export_dir = Path(directory)
            state = harvest_wxmp.BatchState(
                account="测试号",
                output_dir=str(export_dir),
                resume_after=(datetime.now() + timedelta(minutes=10)).isoformat(timespec="seconds"),
            )
            harvest_wxmp.save_batch_state(state, export_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "harvest_wxmp.py"),
                    "--resume",
                    "--output-dir",
                    str(export_dir),
                    "--no-fulltext",
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(result.returncode, 75)
            payload = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(payload["status"], "cooldown")


if __name__ == "__main__":
    unittest.main()
