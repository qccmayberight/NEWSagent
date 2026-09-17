"""已抓取新闻的去重存储。

用新闻链接作为唯一标识，记录在 data/seen.json 中，
避免同一篇新闻在多天日报中重复出现。
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEEN_FILE = DATA_DIR / "seen.json"
MAX_ENTRIES = 5000  # 最多保留的记录数，超出后丢弃最旧的


def load_seen() -> list[str]:
    if not SEEN_FILE.exists():
        return []
    try:
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def filter_new(items: list[dict]) -> list[dict]:
    """从抓取结果中筛掉已经见过的新闻，返回新条目。"""
    seen = set(load_seen())
    return [item for item in items if item["link"] not in seen]


def mark_seen(items: list[dict]) -> None:
    """把本次已使用的新闻标记为已见。"""
    seen = load_seen()
    seen.extend(item["link"] for item in items)
    # 去重且保持顺序，只保留最新的 MAX_ENTRIES 条
    seen = list(dict.fromkeys(seen))[-MAX_ENTRIES:]
    DATA_DIR.mkdir(exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=1), encoding="utf-8")
