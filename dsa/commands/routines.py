"""dsa run / dsa routines — 例行工作流模板。

Usage:
    dsa run morning-routine         盘前例行：大盘复盘 + 自选股扫描 + 简报
    dsa run risk-check              风险扫描
    dsa run earnings-scan           财报季扫描
    dsa routines list               列出可用模板
    dsa routines show <name>        查看模板定义
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml

from ..output import JsonOutput, pass_json


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _load_templates() -> List[Dict[str, Any]]:
    """加载所有内置模板。"""
    if not TEMPLATES_DIR.exists():
        return []
    templates = []
    for f in sorted(TEMPLATES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if data and "name" in data:
                data["_file"] = f.name
                templates.append(data)
        except Exception:
            pass
    return templates


def _find_template(name: str) -> Optional[Dict[str, Any]]:
    """通过名称查找模板。"""
    for t in _load_templates():
        if t["name"] == name:
            return t
    return None


@click.group(name="routines")
def routines() -> None:
    """管理工作流模板。"""


@routines.command(name="list")
@pass_json
def list_templates(json_out: JsonOutput) -> None:
    """列出所有可用模板。"""
    templates = _load_templates()
    if not templates:
        json_out.ok({
            "templates": [],
            "count": 0,
            "message": "No templates found. Check dsa/templates/ directory.",
        })
        return

    result = []
    for t in templates:
        result.append({
            "name": t.get("name"),
            "description": t.get("description", ""),
            "steps": len(t.get("steps", [])),
        })

    json_out.ok({
        "templates": result,
        "count": len(result),
    })


@routines.command()
@click.argument("name")
@pass_json
def show(json_out: JsonOutput, name: str) -> None:
    """查看模板定义详情。"""
    template = _find_template(name)
    if not template:
        json_out.error("NOT_FOUND", f"Template '{name}' not found. Use `dsa routines list` to see available templates.")

    json_out.ok({
        "name": template.get("name"),
        "description": template.get("description", ""),
        "steps": template.get("steps", []),
    })


# ---- dsa run ----

@click.group(name="run")
def run() -> None:
    """执行例行工作流模板。"""


@run.command()
@click.argument("name")
@click.option("--stocks", help="覆盖股票列表（逗号分隔），覆盖模板中的默认标的")
@click.option("--wait", is_flag=True, default=True, help="等待所有步骤完成（默认）")
@click.option("--wait-timeout", type=int, default=900, help="最大等待时间（秒）")
@pass_json
def run_template(
    json_out: JsonOutput,
    name: str,
    stocks: Optional[str],
    wait: bool,
    wait_timeout: int,
) -> None:
    """执行指定的工作流模板。

    注意：当前为 v0.1 实现，仅返回模板定义和步骤清单，不实际执行步骤。
         实际执行引擎（步骤调度、依赖解析、超时控制）将在后续版本实现。
    """
    template = _find_template(name)
    if not template:
        json_out.error("NOT_FOUND", f"Template '{name}' not found. Use `dsa routines list` to see available templates.")

    steps = template.get("steps", [])

    json_out.ok({
        "template": name,
        "description": template.get("description", ""),
        "status": "defined",
        "steps": [
            {
                "name": s.get("name"),
                "description": s.get("description", ""),
                "action": s.get("action"),
                "timeout": s.get("timeout", 60),
                "depends_on": s.get("depends_on", []),
            }
            for s in steps
        ],
        "scope_limitation": "v0.1 仅返回模板定义，步骤实际执行引擎待后续版本实现。Agent 可参考 steps 定义自行编排调用。",
    })
