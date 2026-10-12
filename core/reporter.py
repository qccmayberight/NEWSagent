"""日报渲染与保存。

把 AI 分析结果和原始新闻列表渲染成一份 Markdown 日报，
保存到 reports/ 目录，文件名按日期命名，如 2026-09-17.md。
专题报告存到 reports/topics/，学习报告存到 reports/reads/。
"""

import re
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

CATEGORY_LABELS = {"ai": "AI 行业", "ai_coding": "AI 编程", "economy": "经济行业"}


def render_report(items: list[dict], commentary: str | None) -> str:
    """生成日报的 Markdown 文本。"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# 每日 AI × 经济简报 · {today}\n"]

    lines.append("## AI 分析与讨论\n")
    if commentary:
        lines.append(commentary)
    else:
        lines.append(
            "> 本期未生成 AI 分析（未配置 `MOONSHOT_API_KEY` 或调用失败）。"
            "配置后重跑即可获得分析与讨论。"
        )
    lines.append("\n---\n")

    lines.append("## 原始新闻列表\n")
    for category, label in CATEGORY_LABELS.items():
        lines.append(f"### {label}\n")
        cat_items = [i for i in items if i["category"] == category]
        if not cat_items:
            lines.append("（今日暂无新增）\n")
        for item in cat_items:
            title = item.get("title_zh") or item["title"]
            summary = item.get("summary_zh") or item["summary"]
            lines.append(f"- [{title}]({item['link']}) — *{item['source']}*")
            if summary:
                lines.append(f"  > {summary}")
            if item.get("title_zh"):
                lines.append(f"  > 原文：{item['title']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def save_report(content: str) -> Path:
    """把日报写入 reports/ 目录，返回文件路径。"""
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    path.write_text(content, encoding="utf-8")
    return path


def render_topic_report(keyword: str, items: list[dict], analysis: str | None,
                        style: str = "analysis") -> str:
    """生成专题报告的 Markdown 文本。style 为 "article" 时正文是公众号长文。"""
    today = datetime.now().strftime("%Y-%m-%d")
    label = "公众号文章" if style == "article" else "专题研究"
    lines = [f"# {label} · {keyword} · {today}\n"]

    if style != "article":
        lines.append("## AI 深度分析\n")
    if analysis:
        lines.append(analysis)
    else:
        lines.append(
            "> 本期未生成 AI 内容（未配置 `MOONSHOT_API_KEY` 或调用失败）。"
            "配置后重跑即可获得。"
        )
    lines.append("\n---\n")

    lines.append("## 参考新闻列表\n")
    if not items:
        lines.append("（未检索到相关新闻）\n")
    for item in items:
        title = item.get("title_zh") or item["title"]
        summary = item.get("summary_zh") or item["summary"]
        lines.append(f"- [{title}]({item['link']}) — *{item['source']}*")
        if summary:
            lines.append(f"  > {summary}")
        if item.get("title_zh"):
            lines.append(f"  > 原文：{item['title']}")
    lines.append("")
    return "\n".join(lines) + "\n"


def topic_report_path(keyword: str, article: bool = False) -> Path:
    """专题报告的保存路径（reports/topics/日期-关键词.md，文章版加 -article 后缀）。"""
    slug = keyword.strip().replace(" ", "-")
    suffix = "-article" if article else ""
    return REPORTS_DIR / "topics" / f"{datetime.now().strftime('%Y-%m-%d')}-{slug}{suffix}.md"


def save_topic_report(keyword: str, content: str, article: bool = False) -> Path:
    """把专题报告写入 reports/topics/ 目录，返回文件路径。"""
    path = topic_report_path(keyword, article=article)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def render_read_report(url: str, analysis: str | None) -> str:
    """生成学习报告的 Markdown 文本。"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# 学习分析 · {today}\n"]
    lines.append(f"> 来源：{url}\n")

    lines.append("## AI 解读\n")
    if analysis:
        lines.append(analysis)
    else:
        lines.append(
            "> 本期未生成 AI 内容（未配置 `MOONSHOT_API_KEY` 或调用失败）。"
            "配置后重跑即可获得。"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _url_slug(url: str) -> str:
    """从 URL 生成文件名片段：GitHub 取 owner-repo，其他取域名+路径片段。"""
    text = re.sub(r"^https?://", "", url.strip()).rstrip("/")
    text = re.sub(r"[^0-9A-Za-z一-鿿-]+", "-", text).strip("-")
    return text[:60] or "page"


def read_report_path(url: str) -> Path:
    """学习报告的保存路径（reports/reads/日期-slug.md）。"""
    return REPORTS_DIR / "reads" / f"{datetime.now().strftime('%Y-%m-%d')}-{_url_slug(url)}.md"


def save_read_report(url: str, content: str) -> Path:
    """把学习报告写入 reports/reads/ 目录，返回文件路径。"""
    path = read_report_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
