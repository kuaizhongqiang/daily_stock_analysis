# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note:** This project also has [`AGENTS.md`](AGENTS.md) as the canonical source for AI collaboration rules, governance, PR workflows, and contribution quality standards. When AGENTS.md conflicts with this file, AGENTS.md takes precedence. Run `python scripts/check_ai_assets.py` after modifying AI governance assets.

---

## Project Overview

Stock Intelligent Analysis System — AI-driven stock analysis covering A-shares (China), Hong Kong, and US markets. The system fetches multi-source market data, runs technical analysis + news search, performs LLM-powered analysis via local LM Studio, and generates JSON reports consumed by AI Agent.

This is a **tool/library fork** of [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) that stripped the entire platform layer (Web UI, Desktop app, Bots, notifications, templates, scheduled behaviors) and retained the core analysis engine. The fork has no autonomous behavior — all analysis is triggered on-demand by AI Agent via CLI, MCP, or REST API.

---

## High-Level Architecture

```
main.py (CLI) ──> server.py (FastAPI)
    │                    │
    └── src/core/pipeline.py      ◄── Main workflow orchestration
              │
     ┌────────┼──────────┬─────────────────┐
     │        │          │                 │
data_provider/  src/agent/    src/services/    src/repositories/
(Fetchers)   (Multi-agent) (Business svc)    (Data access)
     │        │          │                 │
     └────────┴──────────┴─────────────────┘
               │
         dsa/ (CLI + MCP Server)
```

### Key Architectural Patterns

1. **Data Source Fallback Chain** (`data_provider/base.py`): Priority-based multi-fetcher with automatic fallback:
   - Priority 0: efinance → Priority 1: akshare → Priority 2: tushare/pytdx → Priority 3: baostock → Priority 4: yfinance → Priority 5: longbridge/tickflow
   - A single fetcher failure doesn't break the pipeline (graceful degradation)

2. **Multi-Agent System** (`src/agent/`):
   - `orchestrator.py` → coordinates specialized agents (decision, intel, technical, risk, portfolio)
   - `executor.py` → routes tasks to skills → skills use tools (data, analysis, search, backtest, market)
   - LLM-agnostic via `litellm` (OpenAI, DeepSeek, Gemini, Claude, Ollama local models)

3. **Strategy-Driven Analysis**: 15+ trading strategies defined as YAML in `strategies/` (MA golden cross, Chan Theory, Wave Theory, bull trend, hot theme, event-driven, growth quality, etc.)

4. **Repository Pattern** (`src/repositories/`): SQLAlchemy-based data access with dedicated repos (alert, analysis, backtest, decision_signal, portfolio, stock)

5. **Pipeline Orchestration** (`src/core/pipeline.py`): The main workflow ties everything together — data fetching → technical analysis → news search → LLM analysis → JSON report generation

### Directory Map

| Directory | Purpose |
|-----------|---------|
| `src/` | Main Python backend — analyzers, core pipeline, agent system, services, schemas, utils |
| `src/core/` | Pipeline orchestration, config registry, backtest engine, market review, trading calendar |
| `src/agent/` | Multi-agent system (orchestrator, executor, agents, skills, tools, strategies) |
| `src/services/` | Business services (analyzer, analysis, alert, portfolio, backtest, decision signal, etc.) |
| `data_provider/` | Multi-source market data fetchers with fallback chain |
| `api/` | FastAPI REST API (v1 endpoints, middlewares, schemas) |
| `strategies/` | YAML trading strategy definitions |
| `tests/` | Flat pytest test suite |
| `scripts/` | Build, CI gate, and utility scripts |
| `docker/` | Dockerfiles |
| `dsa/` | CLI tool + MCP Server (Python package, `pip install -e .`) |

> **Fork changes**: Stripped Web UI, Desktop, Bot channels, notification modules, report templates, Markdown-to-image, scheduled behaviors. No autonomous cron/auto-tag/release — AI Agent triggers all analysis on-demand. Default LLM is local LM Studio (no cloud API required). Integrates via CLI (`dsa`), MCP (`dsa mcp`), OpenClaw Skill, or REST API.

---

## Common Commands

### Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .             # Install dsa CLI + MCP
pip install flake8 pytest    # Dev/test dependencies
```

### Run Analysis

```bash
python main.py                          # Full analysis
python main.py --debug                  # Debug mode (verbose output)
python main.py --dry-run                # Fetch data only, skip analysis
python main.py --stocks 600519,hk00700,AAPL  # Specific stocks
python main.py --market-review          # Market review only
python main.py --serve                  # Analysis + API server
python main.py --serve-only             # API server only
```

### Use CLI / MCP

```bash
# CLI
dsa analyze 600519
dsa market
dsa mcp                              # Start MCP stdio server

# Python module
python -m dsa.mcp_server
```

### Start API Server

```bash
python main.py --serve-only
# OR
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
# Full CI gate (recommended for backend changes)
./scripts/ci_gate.sh

# Offline unit tests only
python -m pytest -m "not network" -v --tb=short

# Specific test markers
python -m pytest -m "unit" -v            # Fast unit tests
python -m pytest -m "integration" -v     # Service-level integration tests
python -m pytest -m "network" -v         # Tests requiring external network

# Python syntax check (minimum validation for backend changes)
python -m py_compile <changed_python_file>

# Single test file
python -m pytest tests/test_specific_file.py -v
```

### Lint / Format

```bash
flake8 . --select=E9,F63,F7,F82    # Critical flake8 checks (used in CI)
black --check .                     # Check formatting (line-length=120)
python -m py_compile <file.py>      # Syntax check
```

### AI Governance Check

```bash
python scripts/check_ai_assets.py    # Validate AGENTS.md / CLAUDE.md symlink / .github instructions relationship
```

### PR / CI Inspection

```bash
gh pr view <pr_number>
gh pr checks <pr_number>
gh run view <run_id> --log-failed
```

---

## Key Technical Details

- **Python 3.10+** required, target versions py310-py312 (black config)
- **Line length**: 120 (black, flake8, isort all configured consistently)
- **Test markers**: `unit`, `integration`, `network` (defined in `setup.cfg`)
- **CI gate** (`scripts/ci_gate.sh`): syntax → flake8 → deterministic tests → offline tests
- **Docker**: Single-stage Python 3.11-slim, non-root `dsa` user
- **`main.py`** auto-configures proxy from `USE_PROXY` env var (skipped in GitHub Actions)

### LLM Configuration

LLM calls are routed through `litellm` (OpenAI-compatible). Default LLM is **local LM Studio** (`http://localhost:1234/v1`). No cloud API key required.

### Data Source Configuration

Data fetchers chain with automatic fallback. Key env vars for each source:
- `AKSHARE_*` (East Money via akshare)
- `TUSHARE_TOKEN` (Tushare Pro)
- `YFINANCE_*` (Yahoo Finance)
- `LONGBRIDGE_*` (Longbridge OpenAPI)
- `SERPAPI_API_KEYS`, `TAVILY_API_KEYS` (news search)

See `.env.example` and `docs/full-guide.md` for complete configuration.

---

## Important Rules from AGENTS.md

- **No auto-commit/push/tag**: Never run `git commit`, `git tag`, or `git push` without explicit confirmation
- **No hardcoded secrets/accounts/paths/model names**
- **Reuse before create**: Prefer existing modules, config entrypoints, scripts, and tests over parallel implementations
- **Stability first**: No refactoring beyond what the current task requires
- **Sync docs when changing config**: Update `.env.example` and related `docs/*.md` when config semantics change
- **Flat CHANGELOG for Unreleased**: `- [type] description` format, no `###` category headers in `[Unreleased]`
- **PRs must include**: what changed, why, validation status, untested items, risks, rollback plan
- **Verification matrix**: Backend → `scripts/ci_gate.sh`; CLI → `dsa --help`; MCP → `python -m dsa.mcp_server`
