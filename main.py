"""NEWSagent 入口。

用法：
     source .venv/bin/activate
    python main.py --once            立即生成一次日报
    python main.py --once --no-ai    立即生成，但不调用 Kimi 做 AI 分析
    python main.py --hours 48        抓取最近 48 小时的新闻
    python main.py --topic Jev       围绕关键词采集新闻并生成专题深度分析
    python main.py --topic Jev --article            输出公众号风格长文
    python main.py --topic Jev --url https://...    把指定文章正文作为参考素材
    python main.py                   常驻运行，每天在 REPORT_TIME（默认 08:00）自动生成
"""

import argparse
import os
import time

import schedule
from dotenv import load_dotenv

from core.pipeline import run_daily_job, run_topic_job

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="每日 AI × 经济新闻 Agent")
    parser.add_argument("--once", action="store_true", help="立即运行一次后退出")
    parser.add_argument("--no-ai", action="store_true", help="跳过 AI 分析，只聚合新闻")
    parser.add_argument("--hours", type=int, default=None, help="抓取最近多少小时的新闻（日报默认 24，专题默认 168）")
    parser.add_argument("--topic", help="围绕指定关键词生成专题深度分析，如 --topic Jev")
    parser.add_argument("--article", action="store_true", help="专题输出为公众号风格长文（配合 --topic 使用）")
    parser.add_argument("--url", action="append", default=[], help="参考文章链接，正文作为专题素材（可多次指定）")
    args = parser.parse_args()

    if args.topic:
        run_topic_job(args.topic, hours=args.hours or 168, use_ai=not args.no_ai,
                      article=args.article, extra_urls=args.url)
        return

    hours = args.hours or 24

    if args.once:
        run_daily_job(hours=hours, use_ai=not args.no_ai)
        return

    report_time = os.getenv("REPORT_TIME", "08:00")
    schedule.every().day.at(report_time).do(run_daily_job, use_ai=not args.no_ai)
    print(f"[调度] 已启动，将每天 {report_time} 自动生成日报。先立即运行一次…")
    run_daily_job(hours=hours, use_ai=not args.no_ai)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
