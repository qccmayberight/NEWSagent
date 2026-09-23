"""关键词专题新闻搜索。

两种搜索通道，按配置自动选择：
1. Kimi 开放平台 REST 接口（POST /v1/tools/search）——适用于 platform.moonshot.cn 的密钥；
2. Anthropic 格式的服务端 web_search 工具（POST {base}/messages）——适用于
   api.kimi.com/coding 订阅端点，搜索由 Kimi 服务端执行，条目的标题和链接直接取自
   真实的搜索结果块，模型回复文本作为补充笔记一并交给分析环节。
搜索结果统一整理成与日报相同的条目结构，供专题分析使用。
"""

import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from config.sources import MAX_SUMMARY_CHARS

load_dotenv()  # 读取 .env 中的 API 密钥等配置

# REST 通道围绕关键词发起多组查询，覆盖新闻、原理、争议、前景等不同角度
QUERY_TEMPLATES = [
    "{keyword} 最新消息",
    "{keyword} 是什么 原理",
    "{keyword} 局限性 争议 质疑",
    "{keyword} 发展前景 影响 案例",
]
RESULTS_PER_QUERY = 20

SEARCH_PROMPT = (
    "请使用 web_search 工具围绕「{keyword}」做一次尽可能全面的资料收集（中文和英文都搜，"
    "覆盖：最新动态、背景原理、局限性/争议/质疑、发展前景/应用案例等不同角度，可换多个角度多搜几次），"
    "然后列出每条的标题、链接、来源媒体、日期和一句话要点。"
)


def _base_url() -> str:
    return os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")


def _detect_language(text: str) -> str:
    """按是否包含汉字粗判中英文。"""
    return "zh" if re.search(r"[一-鿿]", text) else "en"


def _parse_date(date_str: str) -> datetime | None:
    """解析搜索结果里的日期（如 2026-09-17），失败返回 None。"""
    try:
        return datetime.strptime(date_str.strip()[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _make_item(title: str, link: str, summary: str, source: str, date_str: str) -> dict:
    published = _parse_date(date_str)
    return {
        "title": title,
        "link": link,
        "summary": summary[:MAX_SUMMARY_CHARS],
        "published": published.isoformat() if published else "",
        "source": source or "网络搜索",
        "category": "topic",
        "language": _detect_language(title + summary),
    }


def _search_rest(query: str, api_key: str) -> list[dict]:
    """开放平台 REST 搜索接口，返回结构化结果列表。"""
    resp = requests.post(
        _base_url() + "/tools/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"text_query": query, "limit": RESULTS_PER_QUERY, "timeout_seconds": 30},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("search_results", [])


def _collect_via_rest(keyword: str, api_key: str) -> tuple[list[dict], str]:
    """用 REST 接口做多组查询，合并为条目列表。"""
    items: list[dict] = []
    for template in QUERY_TEMPLATES:
        query = template.format(keyword=keyword)
        results = _search_rest(query, api_key)
        print(f"[搜索] 「{query}」: {len(results)} 条")
        for r in results:
            link = (r.get("url") or "").strip()
            title = (r.get("title") or "").strip()
            if link and title:
                items.append(_make_item(
                    title, link, r.get("snippet") or "",
                    (r.get("site_name") or "").strip(), r.get("date") or "",
                ))
    return items, ""


def _collect_via_kimi(keyword: str, api_key: str) -> tuple[list[dict], str]:
    """用 Anthropic 格式的服务端 web_search 收集条目（适用于 coding 订阅端点）。

    返回 (条目列表, 模型的检索笔记)。条目取自真实搜索结果块；
    模型有时会在搜完后继续发起下一轮搜索导致回复被截断，此时笔记为空，
    仅靠条目标题也能完成后续分析。
    """
    resp = requests.post(
        _base_url() + "/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("MOONSHOT_SEARCH_MODEL", "k3"),
            "max_tokens": 8192,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            "messages": [{"role": "user", "content": SEARCH_PROMPT.format(keyword=keyword)}],
        },
        timeout=300,
    )
    resp.raise_for_status()
    blocks = resp.json().get("content", [])

    items: list[dict] = []
    for b in blocks:
        if b.get("type") != "web_search_tool_result":
            continue
        for r in b.get("content", []):
            if not isinstance(r, dict):
                continue
            link = (r.get("url") or "").strip()
            title = (r.get("title") or "").strip()
            if link and title:
                items.append(_make_item(title, link, "", urlparse(link).netloc, ""))

    notes = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    print(f"[搜索] Kimi 联网搜索: {len(items)} 条，笔记 {len(notes)} 字")
    return items, notes


def search_topic(keyword: str, hours: int = 168) -> tuple[list[dict], str]:
    """按关键词搜索相关报道，返回 (条目列表, 检索笔记)，按链接去重并按时间窗口过滤。"""
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key or api_key.startswith("在这里"):
        print("[搜索] 未配置 MOONSHOT_API_KEY，无法进行专题搜索")
        return [], ""

    try:
        items, notes = _collect_via_rest(keyword, api_key)
    except Exception as exc:  # REST 接口不可用（如 coding 订阅端点）时改用服务端 web_search
        print(f"[搜索] REST 搜索不可用（{exc}），改用 Kimi 联网搜索…")
        try:
            items, notes = _collect_via_kimi(keyword, api_key)
        except Exception as exc2:
            print(f"[搜索] Kimi 联网搜索失败: {exc2}")
            return [], ""

    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    seen_links: set[str] = set()
    result: list[dict] = []
    for item in items:
        if item["link"] in seen_links:
            continue
        published = _parse_date(item["published"][:10]) if item["published"] else None
        # 有日期且早于时间窗口的结果跳过；没有日期的保留
        if published and published < cutoff:
            continue
        seen_links.add(item["link"])
        result.append(item)
    return result, notes
