"""日报渲染与保存。

把 AI 分析结果和原始新闻列表渲染成一份 Markdown 日报，
保存到 reports/ 目录，文件名按日期命名，如 2026-09-17.md。
"""

from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

CATEGORY_LABELS = {"ai": "AI 行业", "economy": "经济行业"}


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
