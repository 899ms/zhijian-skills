#!/usr/bin/env python3
import argparse
import json
import html
import os
import re
import ssl
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional

DEFAULT_UA = "Mozilla/5.0 OpenClaw web-clipper"
METASO_API_URL = "https://metaso.cn/api/v1/reader"
JINA_READER_PREFIX = "https://r.jina.ai/"
DEFUDDLE_PACKAGE = "defuddle@0.19.2"


@dataclass
class Article:
    url: str
    title: str
    description: str
    published: str
    author: str
    body_markdown: str
    archive: Optional[str] = None
    extraction_method: str = "static"


class MarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.skip = []
        self.list_stack = []
        self.in_blockquote = 0

    def add(self, text: str = ""):
        self.out.append(text)

    def blank(self):
        text = "".join(self.out)
        if not text.endswith("\n\n"):
            self.out.append("\n\n" if not text.endswith("\n") else "\n")

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "iframe", "svg", "path", "button", "form", "input", "noscript"}:
            self.skip.append(tag)
            return
        if self.skip:
            return
        if tag in {"h1", "h2", "h3", "h4"}:
            self.blank()
            self.add("#" * int(tag[1]) + " ")
        elif tag == "blockquote":
            self.blank()
            self.in_blockquote += 1
            self.add("> ")
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag)
            self.blank()
        elif tag == "li":
            indent = "  " * (len(self.list_stack) - 1)
            bullet = "- " if (not self.list_stack or self.list_stack[-1] == "ul") else "1. "
            self.add(indent + bullet)
        elif tag in {"strong", "b"}:
            self.add("**")
        elif tag in {"em", "i"}:
            self.add("*")
        elif tag == "code":
            self.add("`")
        elif tag == "br":
            self.add("\n")
        elif tag == "hr":
            self.blank()
            self.add("---\n\n")

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        if tag in {"h1", "h2", "h3", "h4", "p", "div", "section", "article", "main"}:
            self.blank()
        elif tag == "blockquote":
            self.in_blockquote = max(0, self.in_blockquote - 1)
            self.blank()
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.blank()
        elif tag == "li":
            self.add("\n")
        elif tag in {"strong", "b"}:
            self.add("**")
        elif tag in {"em", "i"}:
            self.add("*")
        elif tag == "code":
            self.add("`")

    def handle_data(self, data):
        if self.skip:
            return
        text = html.unescape(re.sub(r"\s+", " ", data or ""))
        if not text.strip():
            return
        if text.strip() in {"Subscribe", "Sign in", "Share", "Link", "Close", "close"}:
            return
        if self.in_blockquote:
            prev = "".join(self.out)
            if prev.endswith("\n"):
                self.add("> ")
        self.add(text)

    def markdown(self):
        text = "".join(self.out)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        lines = [ln.rstrip() for ln in text.splitlines()]
        cleaned = []
        prev = None
        for ln in lines:
            s = ln.strip()
            if not s:
                if cleaned and cleaned[-1] != "":
                    cleaned.append("")
                prev = ""
                continue
            if s == prev and (s.startswith("> ") or s.startswith("- ") or s.startswith("1. ")):
                continue
            if s.startswith("Like (") or s.startswith("View comments") or s in {"Share", "Subscribe", "Sign in"}:
                continue
            cleaned.append(ln)
            prev = s
        while cleaned and cleaned[-1] == "":
            cleaned.pop()
        return "\n".join(cleaned).strip() + "\n"


class Clipper:
    def __init__(self, timeout: int = 40, user_agent: str = DEFAULT_UA):
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.user_agent = user_agent

    def fetch(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, context=self.ctx, timeout=self.timeout) as r:
            return r.read().decode("utf-8", errors="ignore")

    def absolute_url(self, base: str, href: str) -> str:
        return urllib.parse.urljoin(base, href)

    def host(self, url: str) -> str:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")

    def prefers_defuddle_first(self, url: str) -> bool:
        host = self.host(url)
        return (
            host in {"x.com", "twitter.com", "mobile.twitter.com", "mp.weixin.qq.com"}
            or host.endswith(".x.com")
            or host.endswith(".weixin.qq.com")
        )

    def prefers_metaso_before_jina(self, url: str) -> bool:
        host = self.host(url)
        return host in {"mp.weixin.qq.com"} or host.endswith(".weixin.qq.com")

    def expand_short_url(self, url: str) -> str:
        host = self.host(url)
        if host != "t.co":
            return url
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent}, method="HEAD")
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=self.timeout) as r:
                return r.geturl() or url
        except urllib.error.HTTPError as e:
            return e.geturl() or url
        except Exception:
            return url

    def x_status_parts(self, url: str) -> Optional[tuple]:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if host not in {"x.com", "twitter.com", "mobile.twitter.com"} and not host.endswith(".x.com"):
            return None
        m = re.match(r"^/([A-Za-z0-9_]{1,15})/(?:status|article)/(\d+)", parsed.path)
        if not m:
            return None
        username = m.group(1)
        if username in {"i", "intent", "share"}:
            return None
        return username, m.group(2)

    def fetch_fxtwitter_status(self, username: str, status_id: str) -> Optional[dict]:
        api_url = f"https://api.fxtwitter.com/{urllib.parse.quote(username)}/status/{status_id}"
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; OpenClaw web-clipper)",
            },
        )
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8", errors="ignore"))
        except Exception:
            return None

    def normalize_x_article_url(self, url: str) -> str:
        url = self.expand_short_url(url)
        parts = self.x_status_parts(url)
        if not parts:
            return url
        username, status_id = parts
        data = self.fetch_fxtwitter_status(username, status_id)
        tweet = data.get("tweet") if isinstance(data, dict) else None
        if not isinstance(tweet, dict) or not tweet.get("article"):
            return url
        author = tweet.get("author") or {}
        screen_name = author.get("screen_name") or username
        tweet_id = tweet.get("id") or status_id
        return f"https://x.com/{screen_name}/article/{tweet_id}"

    def usable_markdown(self, text: Optional[str]) -> bool:
        if not text:
            return False
        stripped = text.strip()
        if len(stripped) < 120:
            return False
        lower = stripped.lower()
        failure_markers = [
            "continue with google",
            "continue with apple",
            "email or username",
            "something went wrong",
            "sign in to x",
            "javascript is not available",
            "enable javascript",
        ]
        if any(marker in lower for marker in failure_markers):
            return False
        return bool(re.search(r"[A-Za-z\u4e00-\u9fff]", stripped))

    def clean_markdown(self, text: str) -> str:
        text = html.unescape(text or "")
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def extract_links(self, page_url: str, html_text: str, count: int, same_origin_only: bool = True, link_pattern: Optional[str] = None) -> List[str]:
        hrefs = re.findall(r'href=\\?"([^\"]+)\\?"', html_text)
        urls = []
        base_host = urllib.parse.urlparse(page_url).netloc
        for href in hrefs:
            full = self.absolute_url(page_url, href)
            if any(x in full for x in ["/comments", "#comments", "/podcast/"]):
                continue
            parsed = urllib.parse.urlparse(full)
            if parsed.scheme not in {"http", "https"}:
                continue
            if same_origin_only and parsed.netloc != base_host:
                continue
            if link_pattern and not re.search(link_pattern, full):
                continue
            if not link_pattern:
                path = parsed.path or ""
                if path in {"", "/"}:
                    continue
                # bias toward article-like URLs
                if path.count("/") < 2:
                    continue
            if full not in urls:
                urls.append(full)
            if len(urls) >= count:
                break
        return urls

    def extract_json_escaped_field(self, html_text: str, field: str) -> Optional[str]:
        marker = f'{field}\\":\\"'
        start = html_text.find(marker)
        if start == -1:
            return None
        i = start + len(marker)
        buf = []
        while i < len(html_text):
            ch = html_text[i]
            if ch == '"':
                bs = 0
                j = i - 1
                while j >= 0 and html_text[j] == "\\":
                    bs += 1
                    j -= 1
                if bs % 2 == 0:
                    break
            buf.append(ch)
            i += 1
        try:
            return json.loads('"' + ''.join(buf) + '"')
        except Exception:
            return None

    def extract_meta(self, html_text: str, prop: str = None, name: str = None) -> str:
        if prop:
            m = re.search(rf'<meta[^>]+property="{re.escape(prop)}"[^>]+content="([^"]+)"', html_text, re.I)
            if m:
                return html.unescape(m.group(1)).strip()
        if name:
            m = re.search(rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]+)"', html_text, re.I)
            if m:
                return html.unescape(m.group(1)).strip()
        return ""

    def extract_json_ld(self, html_text: str) -> List[dict]:
        blocks = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html_text, re.I | re.S)
        docs = []
        for block in blocks:
            raw = block.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    docs.extend([x for x in data if isinstance(x, dict)])
                elif isinstance(data, dict):
                    docs.append(data)
            except Exception:
                continue
        return docs

    def metadata_from_html(self, html_text: str) -> dict:
        title = self.extract_meta(html_text, prop="og:title") or self.extract_meta(html_text, name="twitter:title")
        description = self.extract_meta(html_text, name="description") or self.extract_meta(html_text, prop="og:description")
        published = ""
        author = self.extract_meta(html_text, name="author")

        for field in ["datePublished", "date_created", "post_date"]:
            m = re.search(rf'"{field}":"([^"]+)"', html_text)
            if m:
                published = m.group(1)[:10]
                break

        for doc in self.extract_json_ld(html_text):
            t = doc.get("@type")
            types = t if isinstance(t, list) else [t]
            if any(x in {"Article", "NewsArticle", "BlogPosting"} for x in types):
                title = title or doc.get("headline") or ""
                description = description or doc.get("description") or ""
                date = doc.get("datePublished") or doc.get("dateCreated") or ""
                if date and not published:
                    published = str(date)[:10]
                if not author:
                    a = doc.get("author")
                    if isinstance(a, dict):
                        author = a.get("name") or ""
                    elif isinstance(a, list) and a and isinstance(a[0], dict):
                        author = a[0].get("name") or ""

        return {
            "title": title or "",
            "description": description or "",
            "published": published or "",
            "author": author or "",
        }

    def title_from_markdown(self, markdown: str) -> str:
        for line in markdown.splitlines()[:20]:
            m = re.match(r"^#\s+(.+)$", line.strip())
            if m:
                return m.group(1).strip()
        return ""

    def finish_article(
        self,
        url: str,
        archive: Optional[str],
        metadata: dict,
        body_markdown: str,
        extraction_method: str,
    ) -> Article:
        body_markdown = self.clean_markdown(body_markdown)
        title = metadata.get("title") or self.title_from_markdown(body_markdown)
        title = title or urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1].replace("-", " ")
        published = metadata.get("published") or "unknown-date"
        author = metadata.get("author") or "Unknown"
        return Article(
            url=url,
            title=title,
            description=metadata.get("description") or "",
            published=published,
            author=author,
            body_markdown=body_markdown,
            archive=archive,
            extraction_method=extraction_method,
        )

    def parse_from_html(self, url: str, html_text: str, archive: Optional[str]) -> Optional[Article]:
        metadata = self.metadata_from_html(html_text)
        body_html = None
        for field in ["body_html", "articleBody"]:
            body_html = self.extract_json_escaped_field(html_text, field)
            if body_html:
                break

        if not body_html:
            m = re.search(r'<article[^>]*>(.*?)</article>', html_text, re.I | re.S)
            if not m:
                m = re.search(r'<main[^>]*>(.*?)</main>', html_text, re.I | re.S)
            if m:
                body_html = m.group(1)

        if not body_html:
            return None

        parser = MarkdownParser()
        parser.feed(body_html)
        body_markdown = parser.markdown()
        if not self.usable_markdown(body_markdown):
            return None
        return self.finish_article(url, archive, metadata, body_markdown, "static")

    def parse_via_defuddle(self, url: str, archive: Optional[str]) -> Optional[Article]:
        if not shutil.which("npx"):
            return None
        try:
            result = subprocess.run(
                ["npx", "-y", DEFUDDLE_PACKAGE, "parse", url, "--json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except Exception:
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            data = json.loads(result.stdout)
        except Exception:
            return None

        body_markdown = data.get("contentMarkdown") or data.get("markdown") or ""
        if not body_markdown and data.get("content"):
            parser = MarkdownParser()
            parser.feed(str(data.get("content") or ""))
            body_markdown = parser.markdown()
        if not self.usable_markdown(body_markdown):
            return None

        metadata = {
            "title": data.get("title") or "",
            "description": data.get("description") or "",
            "published": str(data.get("published") or "")[:10],
            "author": data.get("author") or "",
        }
        return self.finish_article(url, archive, metadata, body_markdown, "defuddle")

    def parse_jina_response(self, text: str) -> tuple:
        metadata = {"title": "", "description": "", "published": "", "author": ""}
        lines = text.splitlines()
        body_start = 0
        for idx, line in enumerate(lines):
            if line.startswith("Title: "):
                metadata["title"] = line[len("Title: "):].strip()
            elif line.startswith("Published Time: "):
                metadata["published"] = line[len("Published Time: "):].strip()[:10]
            elif line.startswith("Markdown Content:"):
                body_start = idx + 1
                break
        body = "\n".join(lines[body_start:]).strip()
        return metadata, body

    def parse_via_jina(self, url: str, archive: Optional[str]) -> Optional[Article]:
        try:
            text = self.fetch(JINA_READER_PREFIX + url)
        except Exception:
            return None
        metadata, body_markdown = self.parse_jina_response(text)
        if not self.usable_markdown(body_markdown):
            return None
        return self.finish_article(url, archive, metadata, body_markdown, "jina")

    def fetch_via_metaso(self, url: str) -> Optional[str]:
        """Use Metaso Reader API as fallback. Returns markdown text or None."""
        api_key = os.environ.get("METASO_API_KEY", "")
        if not api_key:
            return None
        payload = json.dumps({"url": url}).encode("utf-8")
        req = urllib.request.Request(
            METASO_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "text/plain",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=self.timeout) as r:
                return r.read().decode("utf-8", errors="ignore")
        except Exception:
            return None

    def parse_via_metaso(self, url: str, archive: Optional[str]) -> Optional[Article]:
        metaso_md = self.fetch_via_metaso(url)
        if not self.usable_markdown(metaso_md):
            return None
        metadata = {"title": self.title_from_markdown(metaso_md or ""), "description": "", "published": "", "author": ""}
        return self.finish_article(url, archive, metadata, metaso_md or "", "metaso")

    def parse_article(self, url: str, archive: Optional[str] = None) -> Article:
        tried = []
        normalized_url = self.normalize_x_article_url(url)
        if normalized_url != url:
            tried.append("x-normalize")
            url = normalized_url

        if self.prefers_defuddle_first(url):
            tried.append("defuddle")
            article = self.parse_via_defuddle(url, archive)
            if article:
                return article

        try:
            tried.append("static")
            html_text = self.fetch(url)
            article = self.parse_from_html(url, html_text, archive)
            if article:
                return article
        except Exception:
            pass

        if self.prefers_metaso_before_jina(url):
            tried.append("metaso")
            article = self.parse_via_metaso(url, archive)
            if article:
                return article

        if "defuddle" not in tried:
            tried.append("defuddle")
            article = self.parse_via_defuddle(url, archive)
            if article:
                return article

        tried.append("jina")
        article = self.parse_via_jina(url, archive)
        if article:
            return article

        if "metaso" not in tried:
            tried.append("metaso")
            article = self.parse_via_metaso(url, archive)
            if article:
                return article

        raise RuntimeError(f"article body not found (tried: {', '.join(tried)})")


def clean_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', ' - ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:180]


def infer_source_kind(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    if host == "mp.weixin.qq.com" or host.endswith(".weixin.qq.com"):
        return "wechat_article"
    if host in {"x.com", "twitter.com", "mobile.twitter.com"} or host.endswith(".x.com"):
        return "x_status"
    return "web_article"


def infer_platform(url: str) -> str:
    source_kind = infer_source_kind(url)
    if source_kind == "wechat_article":
        return "WeChat"
    if source_kind == "x_status":
        return "X"
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    return host or "web"


def dedupe(items: List[str]) -> List[str]:
    result: List[str] = []
    for item in items:
        cleaned = str(item).strip().strip("#")
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def infer_default_topics(article: Article, tags: List[str]) -> List[str]:
    blob = " ".join([article.url, article.title, article.description, " ".join(tags)]).lower()
    topics: List[str] = []
    topic_rules = (
        (("agent", "智能体"), "Agent"),
        (("skill",), "Skill"),
        (("claude code",), "Claude Code"),
        (("codex",), "Codex"),
        (("context engineering", "上下文"), "上下文工程"),
        (("obsidian", "wiki", "knowledge", "理解", "understanding", "cognitive debt"), "知识管理"),
        (("ai training", "ai培训", "培训", "course", "课程"), "AI培训"),
        (("enterprise ai", "企业ai", "企业 ai"), "企业AI落地"),
        (("writing", "content", "公众号", "内容创作"), "内容创作"),
    )
    for keywords, topic in topic_rules:
        if any(keyword in blob for keyword in keywords):
            topics.append(topic)
    return dedupe(topics)


def render_markdown(
    article: Article,
    clipped_at: str,
    tags: List[str],
    training_relevance: str = "medium",
    candidate_outputs: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    compile_status: str = "queued",
) -> str:
    topics = dedupe((topics or []) + infer_default_topics(article, tags))
    candidate_outputs = dedupe(candidate_outputs or ["source_card", "writing_fuel"])
    frontmatter = {
        "type": "source_candidate",
        "title": article.title,
        "author": article.author,
        "source": article.url,
        "resource": article.url,
        "source_kind": infer_source_kind(article.url),
        "platform": infer_platform(article.url),
        "published": article.published,
        "clipped": clipped_at,
        "extractor": article.extraction_method,
        "clipper": "agent_web_clipper",
        "okf_version": "local-okf-v0.2",
        "compile_status": compile_status,
        "status": "unprocessed",
        "training_relevance": training_relevance,
        "topics": topics,
        "candidate_outputs": candidate_outputs,
        "reuse_note": "",
        "tags": tags,
    }
    if article.archive:
        frontmatter["archive"] = article.archive

    lines = ["---"]
    for key in [
        "type",
        "title",
        "author",
        "source",
        "resource",
        "archive",
        "source_kind",
        "platform",
        "published",
        "clipped",
        "extractor",
        "clipper",
        "okf_version",
        "compile_status",
        "status",
        "training_relevance",
        "reuse_note",
    ]:
        if key in frontmatter:
            lines.append(f"{key}: {json.dumps(frontmatter[key], ensure_ascii=False)}")
    for list_key in ["topics", "candidate_outputs", "tags"]:
        values = frontmatter[list_key]
        if values:
            lines.append(f"{list_key}:")
            for value in values:
                lines.append(f"  - {value}")
        else:
            lines.append(f"{list_key}: []")
    lines.append("---\n")
    lines.append(f"# {article.title}\n")
    if article.description:
        lines.append(f"> {article.description}\n")
    lines.append(article.body_markdown)
    return "\n".join(lines).rstrip() + "\n"


def write_article(
    article: Article,
    output_dir: Path,
    clipped_at: str,
    tags: List[str],
    training_relevance: str = "medium",
    candidate_outputs: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    compile_status: str = "queued",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{article.published} {clean_filename(article.title)}.md"
    path = output_dir / filename
    path.write_text(
        render_markdown(
            article,
            clipped_at,
            tags,
            training_relevance=training_relevance,
            candidate_outputs=candidate_outputs,
            topics=topics,
            compile_status=compile_status,
        ),
        encoding="utf-8",
    )
    return path


def load_url_file(path: Path) -> List[str]:
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def validate_http_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"only public HTTP(S) URLs are supported: {url}")
    return url


def main():
    ap = argparse.ArgumentParser(description="Clip one or more web articles to Markdown")
    ap.add_argument("--mode", choices=["single", "batch"], required=True)
    ap.add_argument("--url", help="article URL or index/archive page URL")
    ap.add_argument("--url-file", help="text file with one article URL per line")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--link-pattern", default=None, help="regex to identify article links on batch pages")
    ap.add_argument("--same-origin-only", action="store_true", default=False)
    ap.add_argument("--author", default=None, help="force author name")
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--topic", action="append", default=[], help="OKF topic, repeatable")
    ap.add_argument("--training-relevance", default="medium", choices=["high", "medium", "low", "unknown"], help="OKF training relevance")
    ap.add_argument("--candidate-output", action="append", default=[], help="OKF candidate output, repeatable")
    ap.add_argument("--compile-status", default="queued", help="OKF compile status, default queued")
    ap.add_argument("--summary-json", default=None, help="where to save run summary json")
    args = ap.parse_args()

    if not args.url and not args.url_file:
        print("Need --url or --url-file", file=sys.stderr)
        sys.exit(2)

    clipper = Clipper()
    output_dir = Path(args.output_dir).expanduser()
    clipped_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    tags = ["clipping"] + [t for t in args.tag if t]

    if args.url_file:
        urls = [validate_http_url(url) for url in load_url_file(Path(args.url_file).expanduser())]
        archive_url = args.url if args.mode == "batch" else None
    elif args.mode == "single":
        urls = [validate_http_url(args.url)]
        archive_url = None
    else:
        page_url = validate_http_url(args.url)
        html_text = clipper.fetch(page_url)
        urls = clipper.extract_links(
            page_url,
            html_text,
            count=args.count,
            same_origin_only=args.same_origin_only,
            link_pattern=args.link_pattern,
        )
        archive_url = page_url

    if args.mode == "single":
        urls = urls[:1]
    else:
        urls = urls[: args.count]

    if not urls:
        print("No article URLs found; the link collection layer returned an empty result", file=sys.stderr)
        sys.exit(1)

    results = []
    success = 0
    failed = 0
    for idx, url in enumerate(urls, 1):
        try:
            article = clipper.parse_article(url, archive=archive_url)
            if args.author:
                article.author = args.author
            path = write_article(
                article,
                output_dir,
                clipped_at,
                tags,
                training_relevance=args.training_relevance,
                candidate_outputs=args.candidate_output or None,
                topics=args.topic or None,
                compile_status=args.compile_status,
            )
            results.append({
                "index": idx,
                "ok": True,
                "title": article.title,
                "url": url,
                "path": str(path),
                "extractor": article.extraction_method,
            })
            success += 1
            print(f"OK {idx:02d} {article.title}\t{path}")
        except Exception as e:
            results.append({"index": idx, "ok": False, "url": url, "error": str(e)})
            failed += 1
            print(f"ERR {idx:02d} {url}\t{e}", file=sys.stderr)

    summary = {
        "mode": args.mode,
        "source": args.url,
        "count_requested": args.count,
        "count_attempted": len(urls),
        "success": success,
        "failed": failed,
        "results": results,
    }

    if args.summary_json:
        Path(args.summary_json).expanduser().write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if failed and success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
