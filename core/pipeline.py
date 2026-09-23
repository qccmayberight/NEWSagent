"""每日任务流水线：抓取 → 去重 → 翻译英文新闻 → AI 分析 → 生成日报。"""

from dotenv import load_dotenv

from core.article import fetch_article_text
from core.fetcher import fetch_all
from core.reporter import (
    render_report,
    render_topic_report,
    save_report,
    save_topic_report,
    topic_report_path,
)
from core.search import search_topic
from core.store import filter_new, mark_seen
from core.summarizer import generate_commentary, generate_topic_analysis, generate_topic_article
from core.translator import translate_items

load_dotenv()  # 读取 .env 中的 API 密钥等配置


def run_daily_job(hours: int = 24, use_ai: bool = True) -> None:
    """执行一次完整的日报生成流程。"""
    print("[任务] 开始抓取新闻…")
    items = fetch_all(hours=hours)

    new_items = filter_new(items)
    print(f"[任务] 共 {len(items)} 条，其中新增 {len(new_items)} 条")

    if not new_items:
        print("[任务] 今日无新增新闻，跳过生成日报")
        return

    translate_items(new_items)  # 英文新闻先翻成中文，日报和 AI 分析都使用译文

    commentary = generate_commentary(new_items) if use_ai else None

    path = save_report(render_report(new_items, commentary))
    mark_seen(new_items)
    print(f"[任务] 日报已保存: {path}")


def run_topic_job(keyword: str, hours: int = 168, use_ai: bool = True,
                  article: bool = False, extra_urls: list[str] | None = None) -> None:
    """执行一次专题研究流程：搜索 → 翻译 → AI 生成 → 生成专题报告。

    article=True 时输出公众号风格长文，否则输出结构化深度分析。
    extra_urls 为用户提供的参考文章链接，正文会作为额外素材。
    不写入 seen.json，避免专题搜索结果影响日报的去重。
    """
    print(f"[专题] 开始搜索「{keyword}」相关新闻…")
    items, notes = search_topic(keyword, hours=hours)
    print(f"[专题] 共检索到 {len(items)} 条")

    extra_texts = [text for url in (extra_urls or []) if (text := fetch_article_text(url))]

    if not items and not notes and not extra_texts:
        print("[专题] 未检索到相关素材，已终止")
        return

    translate_items(items)

    if not use_ai:
        analysis = None
    elif article:
        analysis = generate_topic_article(keyword, items, notes, extra_texts)
    else:
        analysis = generate_topic_analysis(keyword, items, notes, extra_texts)

    path = topic_report_path(keyword, article=article)
    if analysis is None and path.exists():
        # 无 AI 内容的报告信息量少，避免覆盖掉已有带分析的同名报告
        print(f"[专题] 本次未生成 AI 内容，保留已有报告: {path}")
        return

    style = "article" if article else "analysis"
    path = save_topic_report(keyword, render_topic_report(keyword, items, analysis, style=style),
                             article=article)
    print(f"[专题] 报告已保存: {path}")
