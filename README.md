# NEWSagent —— 每日 AI × 经济新闻 Agent

每天自动收集 **AI 行业** 与 **经济行业** 的一手新闻，调用 Kimi 大模型进行总结、分析和观点讨论，生成一份 Markdown 日报。目标是帮助你（和你的朋友）用最少的时间紧跟时代、拿到有深度的信息。

## 它是怎么工作的

```
抓取 RSS 新闻源 → 去重（跳过已读） → 英文新闻翻成中文 → Kimi 大模型分析讨论 → 生成 Markdown 日报
```

每天定时自动运行一次，日报保存在 `reports/` 目录，按日期命名（如 `2026-09-17.md`）。

## 目录结构

| 路径 | 作用 |
| --- | --- |
| `main.py` | 程序入口，负责命令行参数与每天定时调度 |
| `config/` | 配置文件：新闻源列表、数量限制 |
| `core/` | 核心代码：抓取、去重、AI 分析、日报生成、任务流水线 |
| `data/` | 运行数据：已读新闻记录（自动生成，无需手动修改） |
| `reports/` | 生成的每日简报（Markdown） |
| `requirements.txt` | Python 依赖清单 |
| `.env.example` | 环境变量模板，复制为 `.env` 后填入自己的密钥 |

每个文件夹里都有一个 `README.md`，详细解释该文件夹中每个文件的作用和功能。

## 快速开始（分享给朋友的步骤）

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置 Kimi API 密钥（去 https://platform.moonshot.cn/ 免费申请）
cp .env.example .env
# 用编辑器打开 .env，把 MOONSHOT_API_KEY 改成自己的密钥

# 3. 立即试跑一次
python main.py --once

# 4. 常驻运行：每天定时（默认 08:00，可在 .env 中改 REPORT_TIME）自动生成日报
python main.py
```

## 常用命令

| 命令 | 说明 |
| --- | --- |
| `python main.py --once` | 立即生成一次日报后退出 |
| `python main.py --once --no-ai` | 只聚合新闻，不调用 AI（不需要密钥） |
| `python main.py --hours 48` | 抓取最近 48 小时的新闻 |
| `python main.py` | 常驻后台，每天定时自动生成 |

## 想换新闻源？

打开 `config/sources.py`，往 `RSS_SOURCES` 列表里加一行 RSS 地址即可，无需改其他代码。

## 说明

- 没有配置 API 密钥也能用：日报照常生成，只是没有 AI 分析和中文翻译。
- 密钥类型说明：开放平台（platform.moonshot.cn）的密钥直接可用；Kimi Code 版（`sk-kim...` 开头）的密钥需要在 `.env` 中加一行 `MOONSHOT_BASE_URL=https://api.kimi.com/coding/v1`（见 `.env.example` 注释）。
- 同一篇新闻不会重复出现在日报里（去重记录在 `data/seen.json`）。
- 定时模式依赖电脑处于开机状态；如果希望关机后也能运行，可以改用系统自带的 `cron` / `launchd` 定时执行 `python main.py --once`。
