"""RSS 新闻抓取模块。

从 config/sources.py 配置的订阅源中抓取最近若干小时的新闻，
统一整理成 {title, link, summary, published, source, category, language} 的字典结构。
"""

import html
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser

from config.sources import MAX_SUMMARY_CHARS, RSS_SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NEWSagent/1.0; +https://github.com/)"
}


def _strip_html(text: str) -> str:
    """去掉摘要里的 HTML 标签并解码转义字符。"""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_time(entry) -> datetime | None:
    """把 RSS 条目的发布时间解析为带时区的 datetime。"""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc)


def fetch_source(source: dict, hours: int = 24) -> list[dict]:
    """抓取单个 RSS 源，返回最近 hours 小时内的新闻列表。"""
    feed = feedparser.parse(source["url"], request_headers=HEADERS)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    items = []
    for entry in feed.entries:
        link = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not link or not title:
            continue
        published = _parse_time(entry)
        # 有发布时间且早于时间窗口的条目跳过；没有时间的条目保留
        if published and published < cutoff:
            continue
        summary = _strip_html(entry.get("summary", ""))[:MAX_SUMMARY_CHARS]
        items.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "published": published.isoformat() if published else "",
                "source": source["name"],
                "category": source["category"],
                "language": source["language"],
            }
        )
    return items


def fetch_all(hours: int = 24) -> list[dict]:
    """抓取所有配置的新闻源，单个源失败不影响其他源。"""
    all_items: list[dict] = []
    for source in RSS_SOURCES:
        try:
            items = fetch_source(source, hours=hours)
            print(f"[抓取] {source['name']}: {len(items)} 条")
            all_items.extend(items)
        except Exception as exc:  # 网络问题或源失效时仅提示
            print(f"[抓取] {source['name']} 失败: {exc}")
    return all_items
