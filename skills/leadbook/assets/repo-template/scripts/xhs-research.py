#!/usr/bin/env python3
"""Collect Xiaohongshu search results through the local xiaohongshu-mcp REST API.

This script is intentionally REST-first because the MCP `search_feeds` tool can
hang while the underlying local HTTP service remains healthy. It turns public
platform signals into a source pack for leadbook research.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:18060"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_base_url(raw: str, *, allow_remote: bool) -> str:
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("--base-url must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("--base-url cannot contain credentials, query, or fragment")
    if not allow_remote and parsed.hostname not in LOOPBACK_HOSTS:
        raise ValueError("--base-url must be loopback unless --allow-remote-base-url is explicit")
    return raw.rstrip("/")


def request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response from {url}: {body[:500]}") from exc

    if parsed.get("success") is False:
        raise RuntimeError(parsed.get("message") or f"Request failed: {url}")
    return parsed


def search_keyword(base_url: str, keyword: str, timeout: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"keyword": keyword})
    url = f"{base_url.rstrip('/')}/api/v1/feeds/search?{query}"
    payload = request_json("GET", url, timeout=timeout)
    feeds = payload.get("data", {}).get("feeds", [])
    return [feed for feed in feeds if feed.get("modelType") == "note"]


def fetch_detail(
    base_url: str,
    feed_id: str,
    xsec_token: str,
    timeout: int,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/feeds/detail"
    payload = request_json(
        "POST",
        url,
        payload={"feed_id": feed_id, "xsec_token": xsec_token},
        timeout=timeout,
    )
    return payload.get("data", {})


def as_int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def text_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").strip()


def note_url(feed_id: str) -> str:
    return f"https://www.xiaohongshu.com/explore/{feed_id}"


def normalize_search_result(keyword: str, feed: dict[str, Any]) -> dict[str, Any]:
    note_card = feed.get("noteCard", {})
    user = note_card.get("user", {})
    interact = note_card.get("interactInfo", {})
    feed_id = text_value(feed.get("id"))
    xsec_token = text_value(feed.get("xsecToken"))

    return {
        "keyword": keyword,
        "feed_id": feed_id,
        "_xsec_token": xsec_token,
        "url": note_url(feed_id) if feed_id else "",
        "title": text_value(note_card.get("displayTitle")) or "(video/no title)",
        "type": text_value(note_card.get("type")),
        "author": text_value(user.get("nickname") or user.get("nickName")),
        "author_id": text_value(user.get("userId")),
        "liked": as_int(interact.get("likedCount")),
        "shared": as_int(interact.get("sharedCount")),
        "comments": as_int(interact.get("commentCount")),
        "collected": as_int(interact.get("collectedCount")),
    }


def merge_detail(item: dict[str, Any], detail: dict[str, Any], *, include_location: bool = False) -> dict[str, Any]:
    note = detail.get("data", {}).get("note", {}) or detail.get("note", {})
    comments = detail.get("data", {}).get("comments", {}) or detail.get("comments", {})
    if note:
        item["title"] = text_value(note.get("title")) or item["title"]
        item["desc"] = text_value(note.get("desc"))
        item["published_at"] = note.get("time")
        item["images"] = note.get("imageList", [])
        if include_location:
            item["ip_location"] = text_value(note.get("ipLocation"))
    if comments:
        item["comment_samples"] = [
            {
                "content": text_value(c.get("content")),
                "like_count": as_int(c.get("likeCount")),
                **({"ip_location": text_value(c.get("ipLocation"))} if include_location else {}),
            }
            for c in comments.get("list", [])[:10]
        ]
    return item


def public_record(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if not key.startswith("_") and key not in {"raw", "detail_raw"}}


def engagement_score(item: dict[str, Any]) -> int:
    return (
        item.get("liked", 0)
        + item.get("collected", 0) * 2
        + item.get("shared", 0) * 3
        + item.get("comments", 0) * 2
    )


def run_collection(args: argparse.Namespace) -> dict[str, Any]:
    health_url = f"{args.base_url.rstrip('/')}/health"
    request_json("GET", health_url, timeout=min(args.timeout, 10))

    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for keyword in args.keywords:
        try:
            feeds = search_keyword(args.base_url, keyword, args.timeout)
        except RuntimeError as exc:
            errors.append({"keyword": keyword, "error": str(exc)})
            continue

        normalized = [normalize_search_result(keyword, feed) for feed in feeds[: args.limit]]
        records.extend(normalized)
        time.sleep(args.pause)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in records:
        feed_id = item.get("feed_id", "")
        if not feed_id or feed_id in seen:
            continue
        seen.add(feed_id)
        deduped.append(item)

    ranked = sorted(deduped, key=engagement_score, reverse=True)
    detail_candidates = sorted(
        [item for item in ranked if item.get("_xsec_token")],
        key=lambda item: (item.get("type") != "normal", -engagement_score(item)),
    )
    successful_details = 0
    for item in detail_candidates:
        if successful_details >= args.details:
            break
        try:
            detail = fetch_detail(
                args.base_url,
                item["feed_id"],
                item["_xsec_token"],
                args.timeout,
            )
            merge_detail(item, detail, include_location=args.include_location)
            successful_details += 1
        except RuntimeError as exc:
            item["detail_error"] = str(exc)
        time.sleep(args.pause)

    return {
        "collected_at": dt.datetime.now().isoformat(timespec="seconds"),
        "base_url": args.base_url,
        "keywords": args.keywords,
        "limit_per_keyword": args.limit,
        "detail_count": args.details,
        "records": [public_record(item) for item in ranked],
        "errors": errors,
    }


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def render_markdown(pack: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Xiaohongshu Research Pack")
    lines.append("")
    lines.append(f"- Collected at: {pack['collected_at']}")
    lines.append(f"- Keywords: {', '.join(pack['keywords'])}")
    lines.append(f"- Records: {len(pack['records'])}")
    lines.append("")

    if pack.get("errors"):
        lines.append("## Collection Errors")
        lines.append("")
        for err in pack["errors"]:
            lines.append(f"- {err['keyword']}: {err['error']}")
        lines.append("")

    lines.append("## High-Signal Notes")
    lines.append("")
    for idx, item in enumerate(pack["records"], start=1):
        title = item.get("title") or "(untitled)"
        lines.append(f"### {idx}. {title}")
        lines.append("")
        lines.append(f"- Keyword: {item.get('keyword', '')}")
        lines.append(f"- Author: {item.get('author', '')}")
        lines.append(f"- Type: {item.get('type', '')}")
        lines.append(
            "- Signals: "
            f"likes {item.get('liked', 0)}, "
            f"collections {item.get('collected', 0)}, "
            f"shares {item.get('shared', 0)}, "
            f"comments {item.get('comments', 0)}"
        )
        lines.append(f"- Feed ID: `{item.get('feed_id', '')}`")
        if item.get("url"):
            lines.append(f"- Source: {item['url']}")
        if item.get("desc"):
            lines.append("")
            lines.append("**Description**")
            lines.append("")
            lines.append(truncate(item["desc"], 1800))
        if item.get("comment_samples"):
            lines.append("")
            lines.append("**Comment Samples**")
            lines.append("")
            for comment in item["comment_samples"][:8]:
                content = truncate(comment["content"], 180)
                likes = comment["like_count"]
                ip = comment.get("ip_location", "")
                suffix = f" ({likes} likes"
                if ip:
                    suffix += f", {ip}"
                suffix += ")"
                lines.append(f"- {content}{suffix}")
        if item.get("detail_error"):
            lines.append("")
            lines.append(f"> Detail fetch failed: {item['detail_error']}")
        lines.append("")

    lines.append("## How To Use In Leadbook")
    lines.append("")
    lines.append("- Put market facts, platform patterns, and count-based observations into `CLAIM_LEDGER.md`.")
    lines.append("- Put reusable examples, counterexamples, and reader situations into `CASE_LIBRARY.md`.")
    lines.append("- Treat Xiaohongshu as demand-side evidence: pain language, objections, hooks, and comments.")
    lines.append("- Do not quote private or sensitive comments in the final book unless they are anonymized and necessary.")
    lines.append("")
    return "\n".join(lines)


def output_stem(keywords: list[str]) -> str:
    today = dt.date.today().isoformat()
    digest = hashlib.sha1("||".join(keywords).encode("utf-8")).hexdigest()[:10]
    return f"{today}-xhs-{digest}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect Xiaohongshu search evidence through local xiaohongshu-mcp REST API."
    )
    parser.add_argument("keywords", nargs="+", help="Search keywords")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="xiaohongshu-mcp REST base URL")
    parser.add_argument(
        "--allow-remote-base-url",
        action="store_true",
        help="Allow sending short-lived detail tokens to a non-loopback service",
    )
    parser.add_argument(
        "--include-location",
        action="store_true",
        help="Persist public IP-location labels; off by default for privacy",
    )
    parser.add_argument("--limit", type=int, default=20, help="Search results per keyword")
    parser.add_argument("--details", type=int, default=5, help="Fetch detail for top N ranked notes")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds")
    parser.add_argument("--pause", type=float, default=1.0, help="Pause between requests")
    parser.add_argument("--out-dir", default="research/xhs", help="Output directory")
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")
    if args.details < 0:
        raise SystemExit("--details must be >= 0")
    if args.timeout < 1:
        raise SystemExit("--timeout must be >= 1")
    if args.pause < 0:
        raise SystemExit("--pause must be >= 0")
    try:
        args.base_url = validate_base_url(args.base_url, allow_remote=args.allow_remote_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    pack = run_collection(args)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(args.keywords)
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(pack), encoding="utf-8")

    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
