"""调用 Kimi（月之暗面）大模型，对当天新闻进行总结与讨论。

使用 Moonshot 的 OpenAI 兼容接口，把当天的新闻标题和摘要一次性发给模型，
让它产出一份有观点、有讨论的中文分析，而不是简单的罗列。
"""

import os

import requests

from config.sources import MAX_ITEMS_PER_CATEGORY


def _api_url() -> str:
    base = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
    return base + "/chat/completions"

SYSTEM_PROMPT = (
    "你是一位资深的 AI 行业与宏观经济分析师，长期跟踪科技产业与全球经济动态。"
    "你的读者是想紧跟时代、拿到一手信息的从业者和爱好者。"
    "请基于我提供的新闻列表进行分析和讨论，要求：\n"
    "1. 不要逐条罗列新闻，而是归纳出真正重要的趋势和信号；\n"
    "2. 给出你自己的判断和讨论，比如这件事为什么重要、可能带来什么影响；\n"
    "3. 如果 AI 与经济的新闻之间存在关联（例如 AI 投资影响市场），请指出来；\n"
    "4. 用简体中文、Markdown 格式输出，包含以下小节：\n"
    "   ## 今日速览（3-5 句话概括）\n"
    "   ## AI 行业动态\n"
    "   ## 经济行业动态\n"
    "   ## 趋势讨论与个人观点\n"
    "   ## 值得持续关注的信号\n"
    "5. 如果新闻不足以支撑某个小节，直接说明即可，不要编造。"
)


def _format_items(items: list[dict]) -> str:
    """把新闻列表整理成发给模型的文本，每个分类限量，避免超出上下文。"""
    lines = []
    count = {"ai": 0, "economy": 0}
    for item in items:
        cat = item["category"]
        if count.get(cat, 0) >= MAX_ITEMS_PER_CATEGORY:
            continue
        count[cat] = count.get(cat, 0) + 1
        label = "AI" if cat == "ai" else "经济"
        title = item.get("title_zh") or item["title"]
        summary = item.get("summary_zh") or item["summary"]
        lines.append(f"- 【{label}｜{item['source']}】{title}\n  摘要：{summary}")
    return "\n".join(lines)


def generate_commentary(items: list[dict]) -> str | None:
    """对当天新闻生成 AI 分析与讨论。

    没有配置 MOONSHOT_API_KEY 或调用失败时返回 None，
    日报仍然生成，只是缺少 AI 分析部分。
    """
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key or api_key.startswith("在这里"):
        print("[AI] 未配置 MOONSHOT_API_KEY，跳过 AI 分析")
        return None
    if not items:
        return None

    model = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "以下是今天抓取到的新闻，请进行分析：\n\n" + _format_items(items)},
        ],
    }
    try:
        resp = requests.post(
            _api_url(),
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        print(f"[AI] 调用 Kimi 失败: {exc}")
        return None
