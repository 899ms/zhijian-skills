from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "clip_articles.py"
SPEC = importlib.util.spec_from_file_location("web_clipper_clip_articles", MODULE_PATH)
assert SPEC and SPEC.loader
clip_articles = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = clip_articles
SPEC.loader.exec_module(clip_articles)


class WebClipperContractTests(unittest.TestCase):
    def test_extracts_article_like_links_and_deduplicates(self) -> None:
        html = """
        <a href="/posts/one">One</a>
        <a href="/posts/one">Duplicate</a>
        <a href="/posts/two#comments">Comments</a>
        <a href="https://other.example/posts/three">Other</a>
        """
        urls = clip_articles.Clipper().extract_links(
            "https://example.com/archive",
            html,
            count=10,
            same_origin_only=True,
        )
        self.assertEqual(["https://example.com/posts/one"], urls)

    def test_static_article_becomes_structured_markdown(self) -> None:
        body = "A sufficiently long public article body. " * 8
        html = f"""
        <html><head>
          <meta property="og:title" content="Example Article">
          <meta name="author" content="Example Author">
          <script type="application/ld+json">{{
            "@type": "Article", "datePublished": "2026-08-04"
          }}</script>
        </head><body><article><p>{body}</p></article></body></html>
        """
        article = clip_articles.Clipper().parse_from_html(
            "https://example.com/posts/example", html, None
        )
        self.assertIsNotNone(article)
        assert article is not None
        rendered = clip_articles.render_markdown(
            article,
            "2026-08-04T10:00:00+08:00",
            ["clipping"],
        )
        self.assertIn('type: "source_candidate"', rendered)
        self.assertIn('title: "Example Article"', rendered)
        self.assertIn('extractor: "static"', rendered)
        self.assertIn('source: "https://example.com/posts/example"', rendered)
        self.assertIn("# Example Article", rendered)

    def test_rejects_non_http_urls(self) -> None:
        for url in ("file:///etc/passwd", "javascript:alert(1)", "example.com/post"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                clip_articles.validate_http_url(url)
        self.assertEqual(
            "https://example.com/post",
            clip_articles.validate_http_url("https://example.com/post"),
        )

    def test_empty_batch_is_a_failure_not_a_false_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            url_file = root / "urls.txt"
            url_file.write_text("\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--mode",
                    "batch",
                    "--url-file",
                    str(url_file),
                    "--output-dir",
                    str(root / "out"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("No article URLs found", result.stderr)

    def test_wrapper_bootstrap_stays_inside_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                ["bash", str(SKILL_ROOT / "scripts" / "run_web_clipper.sh"), "--help"],
                cwd=project,
                env={"PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin", "WEB_CLIPPER_PROJECT_ROOT": str(project)},
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(0, result.returncode, result.stderr or result.stdout)
            self.assertTrue((project / ".web-clipper" / "EXTEND.md").is_file())
            self.assertTrue((project / "Clippings").is_dir())

    def test_wrapper_rejects_parent_output_path_before_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                [
                    "bash",
                    str(SKILL_ROOT / "scripts" / "run_web_clipper.sh"),
                    "--mode",
                    "single",
                    "--url",
                    "https://example.com/post",
                    "--output-dir",
                    "../outside",
                ],
                cwd=project,
                env={"PATH": "/usr/bin:/bin", "WEB_CLIPPER_PROJECT_ROOT": str(project)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("当前项目内的相对路径", result.stderr)
            self.assertFalse((project / ".web-clipper").exists())

    def test_defuddle_dependency_is_version_pinned(self) -> None:
        self.assertEqual("defuddle@0.19.2", clip_articles.DEFUDDLE_PACKAGE)


if __name__ == "__main__":
    unittest.main()
