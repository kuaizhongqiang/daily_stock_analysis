---
applyTo: "api/**,src/**,dsa/**,data_provider/**,server.py,main.py"
---

# Client Instructions

- This is a fork that has stripped Web UI, Desktop app, Bot channels, notifications, and scheduled behaviors. Only the analysis engine remains.
- All analysis is triggered on-demand by AI Agent via CLI (`dsa`), MCP (`dsa mcp`), OpenClaw Plugin, or REST API.
- Changes affecting API fields, auth state, route behavior, or report payloads should be validated against the CLI (`python -m pytest -m 'not network'`), not Web/Desktop.
- No frontend assets, Electron assumptions, or client-side rendering paths exist in this fork.
