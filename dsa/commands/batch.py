"""dsa batch — 批量任务编排。

Usage:
    dsa batch analyze --stocks 600519,000001,300750   批量提交分析
    dsa batch status <batch_id>                       查看批次进度
    dsa batch cancel <batch_id>                       取消整批
    dsa batch ls                                      列出所有批次
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import click

from ..output import JsonOutput, pass_json


# In-memory batch store (v0.1: 进程生命周期内有效)
_batches: Dict[str, Dict[str, Any]] = {}


def _get_or_create_batch(batch_id: str) -> Dict[str, Any]:
    if batch_id not in _batches:
        _batches[batch_id] = {
            "batch_id": batch_id,
            "status": "unknown",
            "jobs": [],
            "created_at": datetime.now().isoformat(),
        }
    return _batches[batch_id]


@click.group(name="batch")
def batch() -> None:
    """批量任务编排。"""


@batch.command()
@click.option("--stocks", "-s", required=True, help="股票代码，逗号分隔（如 600519,000001,300750）")
@click.option("--strategy", "-t", help="交易策略名称（可选）")
@click.option("--wait", is_flag=True, help="等待所有任务完成")
@click.option("--wait-timeout", type=int, default=600, help="最大等待时间（秒）")
@pass_json
def analyze(
    json_out: JsonOutput,
    stocks: str,
    strategy: Optional[str],
    wait: bool,
    wait_timeout: int,
) -> None:
    """批量提交多只股票分析任务。"""
    from src.services.task_queue import AnalysisTaskQueue

    codes = [s.strip() for s in stocks.split(",") if s.strip()]
    if not codes:
        json_out.error("VALIDATION_ERROR", "No stock codes provided")

    batch_id = uuid.uuid4().hex[:12]
    batch_record = _get_or_create_batch(batch_id)
    batch_record["status"] = "running"
    batch_record["stocks"] = codes
    batch_record["started_at"] = datetime.now().isoformat()

    queue = AnalysisTaskQueue()
    jobs = []

    for code in codes:
        try:
            task = queue.submit_task(stock_code=code)
            jobs.append({
                "stock_code": code,
                "job_id": task.task_id,
                "status": task.status,
            })
        except Exception as e:
            jobs.append({
                "stock_code": code,
                "job_id": None,
                "status": "failed",
                "error": str(e),
            })

    batch_record["jobs"] = jobs

    if not wait:
        json_out.ok({
            "batch_id": batch_id,
            "total": len(codes),
            "submitted": sum(1 for j in jobs if j["status"] != "failed"),
            "failed": sum(1 for j in jobs if j["status"] == "failed"),
            "jobs": jobs,
            "message": f"Batch submitted. Use `dsa batch status {batch_id}` to track progress.",
        })
        return

    # Wait mode: poll all jobs until completion or timeout
    deadline = time.time() + wait_timeout
    completed_jobs = []

    while time.time() < deadline:
        pending = 0
        completed_jobs = []

        for j in jobs:
            if j["job_id"] is None:
                completed_jobs.append({**j, "status": "failed"})
                continue

            task = queue.get_task(j["job_id"])
            if task is None:
                completed_jobs.append({**j, "status": "lost"})
                continue

            status = task.status
            if status in ("COMPLETED", "FAILED"):
                completed_jobs.append({
                    "stock_code": j["stock_code"],
                    "job_id": j["job_id"],
                    "status": "completed" if status == "COMPLETED" else "failed",
                    "result": getattr(task, "result", None) if status == "COMPLETED" else None,
                })
            else:
                pending += 1
                completed_jobs.append({**j, "status": status.lower()})

        batch_record["jobs"] = completed_jobs

        if pending == 0:
            batch_record["status"] = "completed"
            json_out.ok({
                "batch_id": batch_id,
                "total": len(codes),
                "completed": sum(1 for j in completed_jobs if j["status"] == "completed"),
                "failed": sum(1 for j in completed_jobs if j["status"] in ("failed", "lost")),
                "jobs": completed_jobs,
                "waited": True,
            })
            return

        time.sleep(3)

    # Timeout
    batch_record["status"] = "timeout"
    json_out.ok({
        "batch_id": batch_id,
        "total": len(codes),
        "completed": sum(1 for j in completed_jobs if j["status"] == "completed"),
        "failed": sum(1 for j in completed_jobs if j["status"] in ("failed", "lost")),
        "pending": sum(1 for j in completed_jobs if j["status"] not in ("completed", "failed", "lost")),
        "jobs": completed_jobs,
        "message": "Wait timeout reached, some jobs still pending. Use `dsa batch status` to check later.",
    })


@batch.command()
@click.argument("batch_id")
@pass_json
def status(json_out: JsonOutput, batch_id: str) -> None:
    """查看批次进度和所有任务状态。"""
    batch_record = _batches.get(batch_id)
    if not batch_record:
        json_out.error("NOT_FOUND", f"Batch {batch_id} not found")

    json_out.ok(batch_record)


@batch.command()
@click.argument("batch_id")
@pass_json
def cancel(json_out: JsonOutput, batch_id: str) -> None:
    """取消整批任务。"""
    batch_record = _batches.get(batch_id)
    if not batch_record:
        json_out.error("NOT_FOUND", f"Batch {batch_id} not found")

    from src.services.task_queue import AnalysisTaskQueue
    queue = AnalysisTaskQueue()

    cancelled = 0
    for j in batch_record.get("jobs", []):
        jid = j.get("job_id")
        if jid and j.get("status") not in ("completed", "failed"):
            try:
                queue.cancel_task(jid)
                cancelled += 1
            except Exception:
                pass

    batch_record["status"] = "cancelled"
    json_out.ok({
        "batch_id": batch_id,
        "status": "cancelled",
        "cancelled_jobs": cancelled,
        "message": f"{cancelled} job(s) cancelled.",
    })


@batch.command(name="ls")
@pass_json
def list_batches(json_out: JsonOutput) -> None:
    """列出所有批次记录。"""
    if not _batches:
        json_out.ok({"batches": [], "count": 0})
        return

    result = [
        {
            "batch_id": bid,
            "status": br["status"],
            "total_jobs": len(br.get("jobs", [])),
            "created_at": br.get("created_at", ""),
        }
        for bid, br in _batches.items()
    ]
    json_out.ok({"batches": result, "count": len(result)})
