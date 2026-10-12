"""RSS 新闻源与运行配置。

想增加 / 删除新闻源，直接改 RSS_SOURCES 列表即可，无需改动其他代码。
"""

# 每个源包含：名称、RSS 地址、所属分类（ai / ai_coding / economy）、语言
RSS_SOURCES = [
    # ---------- AI 行业 ----------
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "ai",
        "language": "en",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "ai",
        "language": "en",
    },
    {
        "name": "MIT Technology Review - AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "category": "ai",
        "language": "en",
    },
    {
        "name": "雷峰网",
        "url": "https://www.leiphone.com/feed",
        "category": "ai",
        "language": "zh",
    },
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/feed",
        "category": "ai",
        "language": "zh",
    },
    # ---------- AI 编程 ----------
    {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "category": "ai_coding",
        "language": "en",
    },
    {
        "name": "Simon Willison's Weblog",
        "url": "https://simonwillison.net/atom/everything/",
        "category": "ai_coding",
        "language": "en",
    },
    # ---------- 经济行业 ----------
    {
        "name": "华尔街见闻",
        "url": "https://dedicated.wallstreetcn.com/rss.xml",
        "category": "economy",
        "language": "zh",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "category": "economy",
        "language": "en",
    },
    {
        "name": "CNBC Economy",
        "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "category": "economy",
        "language": "en",
    },
]

# 每个分类每天最多送入 AI 分析的新闻条数（防止超出模型上下文）
MAX_ITEMS_PER_CATEGORY = 15

# 每条新闻摘要最多保留的字符数
MAX_SUMMARY_CHARS = 200
