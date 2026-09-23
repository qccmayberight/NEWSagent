"""抓取指定网页文章的正文。

用于专题模式：用户提供的参考链接（如微信公众号文章）会被抓取正文，
作为额外素材交给 AI 分析。优先识别微信公众号的正文容器，
其他页面退化为整页去标签提取。
"""

import html
import re

import requests

# 微信等平台会拦截爬虫 UA，这里用浏览器 UA
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

MAX_ARTICLE_CHARS = 6000  # 单篇文章最多保留的正文字符数，避免超出模型上下文


def _strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_article_text(url: str) -> str | None:
    """抓取网页正文文本，失败返回 None。"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[文章] 抓取失败 {url}: {exc}")
        return None

    page = resp.text
    # 微信公众号文章正文在 id="js_content" 的容器里
    match = re.search(r'<div[^>]+id="js_content"[^>]*>([\s\S]*?)</div>\s*<script', page)
    body = match.group(1) if match else page
    text = _strip_html(body)[:MAX_ARTICLE_CHARS]
    if not text:
        print(f"[文章] 未能提取正文: {url}")
        return None
    title_match = re.search(r'<meta property="og:title" content="([^"]*)"', page)
    title = html.unescape(title_match.group(1)) if title_match else url
    print(f"[文章] 已抓取《{title}》: {len(text)} 字")
    return f"《{title}》（{url}）\n{text}"
