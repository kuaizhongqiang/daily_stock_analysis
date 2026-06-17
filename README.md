<div align="center">

# 📈 股票智能分析系统

> **Fork 说明**：本项目基于 [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)（MIT License）修改而来。
> 原始项目是一个功能完备的 AI 股票分析平台，包含 Web UI、桌面端、多 Bot 渠道等。
> 本 Fork 的核心变更：
> - 🧹 **彻底剥离平台层** — 已移除 Web UI、桌面端、Bot 渠道、通知推送
> - 🤖 **AI Agent 驱动** — 由蜜蜜（AI Agent）通过 CLI/MCP 调用，输出结构化 JSON，不再面向人用
> - 🔌 **保留核心分析引擎** — 多市场数据聚合、AI 决策分析、策略系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

</div>

---

## ✨ 核心能力

| 能力 | 覆盖内容 |
|------|---------|
| AI 决策报告 | 核心结论、评分、趋势、买卖点位、风险警报、催化因素、操作检查清单 |
| 多市场数据聚合 | A股、港股、美股、ETF；行情、K 线、技术指标、资金流、筹码、新闻、公告和基本面 |
| 策略系统 | 均线金叉、缠论、波浪理论、多头趋势、热点题材、事件驱动、成长质量、预期重估等 15+ 策略 |
| Agent 问股 | 多轮追问，策略驱动的分析对话，支持自定义策略 YAML |

### 数据来源

| 类型 | 支持 |
|------|------|
| AI 模型 | OpenAI 兼容（DeepSeek、通义千问、Gemini、Claude 等）、Ollama 本地模型 |
| 行情数据 | AkShare、Tushare、Pytdx、Baostock、YFinance、LongBridge、TickFlow |
| 新闻搜索 | SerpAPI、Tavily、Brave、博查、SearXNG |

---

## 🚀 快速开始

```bash
# 克隆
git clone https://github.com/kuaizhongqiang/daily_stock_analysis.git && cd daily_stock_analysis

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env && vim .env

# 运行分析（JSON 输出）
python main.py
```

常用命令：

```bash
python main.py --debug              # 调试模式
python main.py --dry-run            # 干跑
python main.py --stocks 600519,hk00700,AAPL   # 指定股票
python main.py --market-review      # 仅大盘复盘
```

---

## ⚙️ 配置说明

完整环境变量、模型渠道、数据源优先级、交易纪律等见 [完整配置指南](docs/full-guide.md)。

关键配置项：

| 环境变量 | 说明 |
|---------|------|
| `STOCK_LIST` | 自选股代码，如 `600519,hk00700,AAPL` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | AI 模型 API（兼容 DeepSeek、通义千问等） |
| `SERPAPI_API_KEYS` | 新闻搜索 API |
| `TAVILY_API_KEYS` | 新闻搜索 API |

---

## 📄 License

[MIT License](LICENSE)

- Copyright © 2026 **ZhuLinsen**（原始作者）
- Copyright © 2026 **kuaizhongqiang**（Fork 修改）

原始版权声明和许可协议保持完整，详见 [LICENSE](LICENSE)。

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。
