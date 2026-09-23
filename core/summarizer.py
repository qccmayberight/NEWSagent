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

TOPIC_SYSTEM_PROMPT = (
    "你是一位前沿技术与新概念的研究分析师，擅长从零散报道中梳理出一个技术或概念的全貌。"
    "你的读者想深入理解一个刚听说的新事物，并判断它的真实价值。"
    "请围绕指定关键词，基于我提供的新闻列表进行深度分析，要求：\n"
    "1. 严格区分\"报道中的事实\"和\"你的推测判断\"，推测部分要明确标注；\n"
    "2. 用简体中文、Markdown 格式输出，包含以下小节：\n"
    "   ## 这是什么（背景与核心原理）\n"
    "   ## 当前进展与关键事实\n"
    "   ## 局限性分析\n"
    "   ## 发展前景与可能路径\n"
    "   ## 争议与风险\n"
    "   ## 值得持续关注的信号\n"
    "3. 如果新闻不足以支撑某个小节，直接说明即可，不要编造；\n"
    "4. 报道中厂商自己宣称的数据（如性能提升倍数）要注明出处和口径，不能直接当作定论。"
)

ARTICLE_SYSTEM_PROMPT = (
    "你是一位顶尖的科技专栏作者，长期为优质公众号撰写深度稿件，"
    "擅长把前沿技术和新概念讲得既准确又好看。"
    "请围绕指定关键词，基于我提供的素材写一篇可直接发布的中文公众号长文，要求：\n"
    "1. 起一个吸引人的标题（作为一级标题），开头用一段导语勾住读者；\n"
    "2. 正文用小标题分段，讲清楚：它是什么、为什么突然火了、背后的原理、"
    "   真实能力与局限、争议点、未来可能怎么发展；\n"
    "3. 语言通俗生动，可以打比方、讲故事，但关键事实必须忠于素材，"
    "   厂商宣称的数据要注明口径，推测内容要明示是推测；\n"
    "4. 适当引用素材中的具体细节（数字、人名、事件），让文章有据可依；\n"
    "5. 结尾给出你自己的判断和读者可以持续关注的观察点；\n"
    "6. 篇幅 2000-3500 字，Markdown 格式，素材不足时如实说明，不要编造。"
)

# 专题分析最多送入模型的新闻条数
MAX_TOPIC_ITEMS = 25


def _call_kimi(system_prompt: str, user_content: str) -> str | None:
    """调用 Kimi 生成内容，未配置密钥或失败时返回 None。"""
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key or api_key.startswith("在这里"):
        print("[AI] 未配置 MOONSHOT_API_KEY，跳过 AI 分析")
        return None
    model = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
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
    if not items:
        return None
    return _call_kimi(SYSTEM_PROMPT, "以下是今天抓取到的新闻，请进行分析：\n\n" + _format_items(items))


def _build_topic_materials(keyword: str, items: list[dict], notes: str, extra_texts: list[str]) -> str | None:
    """把检索条目、检索笔记和参考文章正文拼成发给模型的素材文本。"""
    if not items and not notes and not extra_texts:
        return None
    parts = []
    lines = []
    for item in items[:MAX_TOPIC_ITEMS]:
        title = item.get("title_zh") or item["title"]
        summary = item.get("summary_zh") or item["summary"]
        lines.append(f"- 【{item['source']}】{title}\n  摘要：{summary}")
    if lines:
        parts.append("检索到的相关报道：\n" + "\n".join(lines))
    if notes:
        parts.append("搜索阶段的检索笔记：\n" + notes)
    for text in extra_texts:
        parts.append("参考文章正文：\n" + text)
    return f"请围绕关键词「{keyword}」，基于以下材料：\n\n" + "\n\n".join(parts)


def generate_topic_analysis(keyword: str, items: list[dict], notes: str = "",
                            extra_texts: list[str] | None = None) -> str | None:
    """围绕关键词生成专题深度分析，失败时返回 None。

    notes 为搜索阶段模型返回的检索笔记（含各报道的要点），可为空；
    extra_texts 为用户提供的参考文章正文列表。
    """
    user_content = _build_topic_materials(keyword, items, notes, extra_texts or [])
    if not user_content:
        return None
    user_content += "\n\n请进行深度分析。"
    return _call_kimi(TOPIC_SYSTEM_PROMPT, user_content)


def generate_topic_article(keyword: str, items: list[dict], notes: str = "",
                           extra_texts: list[str] | None = None) -> str | None:
    """围绕关键词生成公众号风格的长文，失败时返回 None。"""
    user_content = _build_topic_materials(keyword, items, notes, extra_texts or [])
    if not user_content:
        return None
    user_content += "\n\n请写一篇公众号长文。"
    return _call_kimi(ARTICLE_SYSTEM_PROMPT, user_content)
