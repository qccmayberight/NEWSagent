"""每日任务流水线：抓取 → 去重 → 翻译英文新闻 → AI 分析 → 生成日报。"""

from dotenv import load_dotenv

from core.fetcher import fetch_all
from core.reporter import render_report, save_report
from core.store import filter_new, mark_seen
from core.summarizer import generate_commentary
from core.translator import translate_items

load_dotenv()  # 读取 .env 中的 API 密钥等配置


def run_daily_job(hours: int = 24, use_ai: bool = True) -> None:
    """执行一次完整的日报生成流程。"""
    print("[任务] 开始抓取新闻…")
    items = fetch_all(hours=hours)

    new_items = filter_new(items)
    print(f"[任务] 共 {len(items)} 条，其中新增 {len(new_items)} 条")

    translate_items(new_items)  # 英文新闻先翻成中文，日报和 AI 分析都使用译文

    commentary = generate_commentary(new_items) if use_ai else None

    path = save_report(render_report(new_items, commentary))
    mark_seen(new_items)
    print(f"[任务] 日报已保存: {path}")
