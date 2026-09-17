"""英文新闻的机器翻译。

把英文新闻的标题和摘要批量发给 Kimi 翻译成简体中文，
译文保存在条目的 title_zh / summary_zh 字段中，供日报渲染和 AI 分析使用。
没有配置密钥或翻译失败时自动保留英文原文，不影响日报生成。
"""

import json
import os
import re

import requests

def _api_url() -> str:
    base = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
    return base + "/chat/completions"
BATCH_SIZE = 20  # 每批翻译的条数，过多容易超出模型输出长度

PROMPT = (
    "你是专业的科技与财经新闻翻译。下面是一个 JSON 数组，每个元素包含英文新闻的 id、标题和摘要。"
    "请逐条翻译成简体中文：标题简洁通顺，摘要保留关键信息和数字。"
    "只输出一个 JSON 数组，不要输出任何其他内容，格式："
    '[{"id": 0, "title": "中文标题", "summary": "中文摘要"}, ...]'
)


def _translate_batch(batch: list[dict], model: str, api_key: str) -> dict[int, dict]:
    """翻译一批条目，返回 {序号: 译文}。"""
    payload_items = [
        {"id": idx, "title": item["title"], "summary": item["summary"]}
        for idx, item in enumerate(batch)
    ]
    resp = requests.post(
        _api_url(),
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": json.dumps(payload_items, ensure_ascii=False)},
            ],
        },
        timeout=180,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    # 模型有时会把 JSON 包在 ```json 代码块里，提取出数组部分再解析
    match = re.search(r"\[.*\]", text, re.S)
    data = json.loads(match.group(0)) if match else []
    return {entry["id"]: entry for entry in data if isinstance(entry, dict) and "id" in entry}


def translate_items(items: list[dict]) -> None:
    """就地翻译列表中英文条目的标题和摘要。"""
    en_items = [item for item in items if item.get("language") == "en"]
    if not en_items:
        return
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key or api_key.startswith("在这里"):
        print(f"[翻译] 未配置 MOONSHOT_API_KEY，{len(en_items)} 条英文新闻保留原文")
        return

    model = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
    for start in range(0, len(en_items), BATCH_SIZE):
        batch = en_items[start : start + BATCH_SIZE]
        try:
            result = _translate_batch(batch, model, api_key)
            for idx, item in enumerate(batch):
                translation = result.get(idx)
                if translation:
                    item["title_zh"] = translation.get("title", "")
                    item["summary_zh"] = translation.get("summary", "")
            print(f"[翻译] 已翻译 {start + len(batch)}/{len(en_items)} 条英文新闻")
        except Exception as exc:  # 翻译失败时该批保留原文
            print(f"[翻译] 第 {start // BATCH_SIZE + 1} 批翻译失败: {exc}")
