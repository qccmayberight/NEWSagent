# core/ —— 核心代码文件夹

这里是 Agent 的“大脑”，一次日报的完整流程由这几个文件接力完成：

```
fetcher.py（抓新闻）→ store.py（去重）→ translator.py（英译中）→ summarizer.py（AI 分析）→ reporter.py（生成日报）
                      ↑ pipeline.py 负责把这几步串起来
```

## 文件说明

### `fetcher.py` —— 新闻抓取

**作用**：读取 `config/sources.py` 里配置的所有 RSS 源，抓取最近 24 小时（可调）内发布的新闻。

**关键功能**：
- `fetch_source(source, hours)`：抓取单个源，把每条新闻整理成统一格式（标题、链接、摘要、发布时间、来源、分类）。
- `fetch_all(hours)`：抓取全部源。某个源失败（网络问题、源失效）只打印提示，不影响其他源。
- 自动清洗摘要中的 HTML 标签，并按发布时间过滤旧闻；每个源最多保留 `MAX_ITEMS_PER_SOURCE` 条，防止单个高频源淹没日报。

### `store.py` —— 去重存储

**作用**：保证同一篇新闻不会重复出现在日报里。

**关键功能**：
- `load_seen()` / `mark_seen()`：读取、写入已见新闻的链接记录（保存在 `data/seen.json`）。
- `filter_new(items)`：从抓取结果中筛掉已经上过日报的新闻。

### `summarizer.py` —— AI 分析与讨论

**作用**：把当天新闻发给 Kimi（月之暗面）大模型，让它以“资深 AI 分析师”的口吻输出有观点的分析（聚焦 AI 产品与应用落地，金融新闻只保留与 AI 直接相关的部分），而不是简单罗列。

**关键功能**：
- `generate_commentary(items)`：调用 Moonshot 的 OpenAI 兼容接口，返回 Markdown 格式的分析（今日速览 / AI 行业动态 / AI 应用动态 / AI 编程动态 / AI 相关的经济信号 / 趋势讨论 / 值得关注的信号）。
- 没配置 `MOONSHOT_API_KEY` 或调用失败时返回 `None`，日报照常生成，只是没有 AI 部分。
- `SYSTEM_PROMPT`：定义 AI 的角色和输出格式，想让 AI 换个分析风格就改这里。

### `translator.py` —— 英文新闻翻译

**作用**：把英文新闻的标题和摘要批量发给 Kimi 翻译成简体中文，让日报从头到尾都是中文。

**关键功能**：
- `translate_items(items)`：筛出 `language` 为 `"en"` 的条目，分批（每批 20 条）发给 Kimi 翻译，译文写回条目的 `title_zh` / `summary_zh` 字段。
- 翻译后的内容同时用于日报展示和 AI 分析（让 Kimi 分析时读中文，输出质量更稳定）。
- 没配置 `MOONSHOT_API_KEY` 或翻译失败时保留英文原文，不影响日报生成。

### `reporter.py` —— 日报生成

**作用**：把 AI 分析和原始新闻列表拼成一份 Markdown 日报。

**关键功能**：
- `render_report(items, commentary)`：生成日报文本，上半部分是 AI 分析，下半部分是按分类整理的原始新闻（带链接，方便点进去看原文）。
- `save_report(content)`：保存到 `reports/` 目录，文件名是当天日期。

### `pipeline.py` —— 任务流水线

**作用**：把上面四步按顺序串起来的“总调度”。

**关键功能**：
- `run_daily_job(hours, use_ai)`：抓取 → 去重 → AI 分析 → 渲染 → 保存 → 标记已读。`main.py` 和定时器调用的都是这个函数。
- `run_topic_job(keyword, ...)`：专题研究流程，围绕关键词搜索报道并生成深度分析或公众号长文。
- `run_read_job(url, use_ai)`：学习模式流程，抓取 → AI 解读 → 保存报告到 `reports/reads/`。
- 启动时自动加载根目录 `.env` 中的密钥配置。

### `reader.py` —— 学习模式内容提取

**作用**：为 `--learn` 命令提取素材。GitHub 仓库链接走公开 REST API（元数据 + README + 根目录结构），普通网页复用 `article.py` 的正文提取。

**关键功能**：
- `fetch_learning_material(url)`：按 URL 类型自动选择提取方式。
- `fetch_github_repo(url)`：抓取仓库描述、stars、主语言、topics、根目录文件列表和 README 原文。配置 `GITHUB_TOKEN` 环境变量可提高 API 限额。

### `__init__.py`

**作用**：Python 包标记文件（空文件），让 `core` 可以被当作模块包导入。不要删除。
