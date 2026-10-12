"""学习模式的内容提取：网页文章或 GitHub 仓库。

普通网页复用 core/article.py 的正文提取；GitHub 仓库主页则通过
公开 REST API 抓取元数据、README 和根目录结构，拼成一份素材文本，
供 AI 做内容总结与见解分析。无需鉴权即可访问公共仓库，
配置 GITHUB_TOKEN 环境变量可提高 API 限额。
"""

import os
import re

import requests

from core.article import fetch_article_text

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Mozilla/5.0 (compatible; NEWSagent/1.0; +https://github.com/)",
}

MAX_README_CHARS = 8000  # README 最多保留的字符数，避免超出模型上下文

_GITHUB_REPO_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)")


def _github_headers() -> dict:
    headers = dict(HEADERS)
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, accept: str | None = None) -> requests.Response | None:
    headers = _github_headers()
    if accept:
        headers["Accept"] = accept
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp
    except Exception as exc:
        print(f"[学习] GitHub 请求失败 {url}: {exc}")
        return None


def fetch_github_repo(url: str) -> str | None:
    """抓取 GitHub 仓库的元数据、README 和根目录结构，失败返回 None。"""
    match = _GITHUB_REPO_RE.match(url.strip())
    if not match:
        return None
    owner, repo = match.groups()
    repo = repo.removesuffix(".git")
    api = f"https://api.github.com/repos/{owner}/{repo}"

    resp = _get(api)
    if resp is None:
        return None
    meta = resp.json()

    lines = [
        f"GitHub 仓库：{meta.get('full_name', f'{owner}/{repo}')}（{url}）",
        f"描述：{meta.get('description') or '（无）'}",
        f"Stars：{meta.get('stargazers_count', 0)}，Forks：{meta.get('forks_count', 0)}",
        f"主语言：{meta.get('language') or '（未知）'}",
        f"Topics：{', '.join(meta.get('topics') or []) or '（无）'}",
        f"License：{(meta.get('license') or {}).get('spdx_id') or '（无）'}",
        f"创建时间：{meta.get('created_at', '')}，最近更新：{meta.get('pushed_at', '')}",
    ]

    resp = _get(api + "/contents")
    if resp is not None and isinstance(resp.json(), list):
        entries = [e["name"] + ("/" if e["type"] == "dir" else "") for e in resp.json()]
        lines.append("根目录结构：" + ", ".join(entries))

    resp = _get(api + "/readme", accept="application/vnd.github.raw")
    if resp is not None and resp.text.strip():
        lines.append("README 正文（可能截断）：\n" + resp.text.strip()[:MAX_README_CHARS])
    else:
        lines.append("（该仓库没有 README 或抓取失败）")

    text = "\n".join(lines)
    print(f"[学习] 已抓取仓库 {owner}/{repo}: {len(text)} 字")
    return text


def fetch_learning_material(url: str) -> str | None:
    """抓取学习素材：GitHub 仓库走 API，其他网页走正文提取。"""
    if _GITHUB_REPO_RE.match(url.strip()):
        return fetch_github_repo(url)
    return fetch_article_text(url)
