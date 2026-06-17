# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note:** This project also has [`AGENTS.md`](AGENTS.md) as the canonical source for AI collaboration rules, governance, PR workflows, and contribution quality standards. When AGENTS.md conflicts with this file, AGENTS.md takes precedence. Run `python scripts/check_ai_assets.py` after modifying AI governance assets.

---

## Project Overview

Stock Intelligent Analysis System — AI-driven stock analysis covering A-shares (China), Hong Kong, and US markets. The system fetches multi-source market data, runs technical analysis + news search, performs LLM-powered analysis, generates reports, and sends notifications.

This is a **tool/library fork** of [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) that stripped the platform layer (standalone Web UI, Desktop app, Bots) and retained the core analysis engine, integrated with an AI Agent for scheduling and interaction.

---

## High-Level Architecture

```
main.py (CLI) ──> server.py (FastAPI)
    │                    │
    └── src/core/pipeline.py      ◄── Main workflow orchestration (143KB)
              │
     ┌────────┼──────────┬─────────────────┐
     │        │          │                 │
data_provider/  src/agent/    src/services/    src/repositories/
(Fetchers)   (Multi-agent) (Business svc)    (Data access)
     │        │          │                 │
     └────────┴──────────┴─────────────────┘
               │
         templates/ (Jinja2 reports)
               │
         notification.py (Feishu, DingTalk, Discord, etc.)
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

5. **Pipeline Orchestration** (`src/core/pipeline.py`): The main 143KB workflow ties everything together — data fetching → technical analysis → news search → LLM analysis → report generation → notification

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
| `docker/` | Dockerfile + docker-compose |

> **Removed**: Web UI (`apps/dsa-web/`), Desktop (`apps/dsa-desktop/`), notification modules (`src/notification*`), report templates (`templates/`), Markdown-to-image (`src/md2img.py`), Bot channels (`bot/`). The project no longer has a human-facing UI — all output is structured JSON consumed by AI Agent.

---

## Common Commands

### Install Dependencies

```bash
pip install -r requirements.txt
pip install flake8 pytest    # Dev/test dependencies
cd apps/dsa-web && npm ci    # Web frontend
```

### Run Analysis

```bash
python main.py                          # Full analysis
python main.py --debug                  # Debug mode (verbose output)
python main.py --dry-run                # Fetch data only, skip analysis/push
python main.py --stocks 600519,hk00700,AAPL  # Specific stocks
python main.py --market-review          # Market review only
python main.py --schedule               # Scheduled mode (infinite loop)
python main.py --serve                  # Analysis + API server
python main.py --serve-only             # API server only
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

### Web Frontend (when modifying `apps/dsa-web/`)

```bash
cd apps/dsa-web
npm run dev          # Vite dev server (hot reload)
npm run build        # TypeScript check + Vite production build
npm run lint         # ESLint
npm run test         # Vitest unit tests
npm run test:smoke   # Playwright smoke tests
```

### Desktop (when modifying `apps/dsa-desktop/`)

```bash
cd apps/dsa-desktop
npm run dev          # Run Electron dev
npm run build        # electron-builder packaging
npm run test         # Node test runner
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
- **Docker**: Multi-stage (Node 20 web builder + Python 3.11-slim-bookworm runtime), non-root `dsa` user, includes `wkhtmltopdf` for markdown-to-image
- **`main.py`** auto-configures proxy from `USE_PROXY` env var (skipped in GitHub Actions)

### LLM Configuration

LLM calls are routed through `litellm` (OpenAI-compatible). Key env vars:
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` — primary AI API
- Supports DeepSeek, Tongyi Qianwen, Gemini, Claude, Ollama local models

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
- **Verification matrix**: Backend → `scripts/ci_gate.sh`; Web → `npm run lint + npm run build`; Desktop → build web first
