"""NEWSagent 入口。

用法：
    python main.py --once            立即生成一次日报
    python main.py --once --no-ai    立即生成，但不调用 Kimi 做 AI 分析
    python main.py --hours 48        抓取最近 48 小时的新闻
    python main.py                   常驻运行，每天在 REPORT_TIME（默认 08:00）自动生成
"""

import argparse
import os
import time

import schedule
from dotenv import load_dotenv

from core.pipeline import run_daily_job

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="每日 AI × 经济新闻 Agent")
    parser.add_argument("--once", action="store_true", help="立即运行一次后退出")
    parser.add_argument("--no-ai", action="store_true", help="跳过 AI 分析，只聚合新闻")
    parser.add_argument("--hours", type=int, default=24, help="抓取最近多少小时的新闻（默认 24）")
    args = parser.parse_args()

    if args.once:
        run_daily_job(hours=args.hours, use_ai=not args.no_ai)
        return

    report_time = os.getenv("REPORT_TIME", "08:00")
    schedule.every().day.at(report_time).do(run_daily_job, use_ai=not args.no_ai)
    print(f"[调度] 已启动，将每天 {report_time} 自动生成日报。先立即运行一次…")
    run_daily_job(hours=args.hours, use_ai=not args.no_ai)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
