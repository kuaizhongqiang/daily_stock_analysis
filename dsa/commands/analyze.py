"""dsa analyze / submit / status / result / cancel / jobs commands."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import click

from ..output import JsonOutput, pass_json


@click.group(name="analyze")
def analyze() -> None:
    """Analyze a stock."""


@analyze.command()
@click.argument("stock_code")
@click.option("--strategy", "-s", help="Trading strategy name")
@click.option("--force", is_flag=True, help="Force re-analysis, ignore cache")
@click.option("--session", help="Session ID for context-aware analysis")
@pass_json
def analyze_stock(json_out: JsonOutput, stock_code: str, strategy: Optional[str], force: bool, session: Optional[str]) -> None:
    """Analyze a single stock (sync, waits for result)."""
    from src.core.pipeline import StockAnalysisPipeline
    from src.config import get_config

    # Track session context
    if session:
        from src.agent.conversation import conversation_manager
        sess = conversation_manager.get_or_create(session)
        sess.update_context("last_stock", stock_code)

    config = get_config()
    pipeline = StockAnalysisPipeline(config)
    results = pipeline.run(stock_codes=[stock_code], dry_run=False)
    if results:
        r = results[0]
        result = {
            "stock_code": stock_code,
            "score": getattr(r, "sentiment_score", None),
            "action": getattr(r, "action", None),
            "decision_type": getattr(r, "decision_type", None),
            "confidence_level": getattr(r, "confidence_level", None),
            "trend_prediction": getattr(r, "trend_prediction", None),
            "operation_advice": getattr(r, "operation_advice", None),
            "summary": getattr(r, "analysis_summary", ""),
        }
        if session:
            result["session_id"] = session
        json_out.ok(result)
    else:
        json_out.error("ANALYSIS_FAILED", "No analysis result returned")


@click.group(name="submit")
def submit() -> None:
    """Submit an async analysis job."""


@submit.command()
@click.argument("stock_code")
@click.option("--strategy", "-s", help="Trading strategy name")
@click.option("--session", help="Session ID for context-aware analysis")
@pass_json
def submit_stock(json_out: JsonOutput, stock_code: str, strategy: Optional[str], session: Optional[str]) -> None:
    """Submit stock analysis asynchronously, returns job_id immediately."""
    from src.services.task_queue import AnalysisTaskQueue

    if session:
        from src.agent.conversation import conversation_manager
        sess = conversation_manager.get_or_create(session)
        sess.update_context("last_stock", stock_code)

    queue = AnalysisTaskQueue()
    try:
        task = queue.submit_task(stock_code=stock_code)
        result = {
            "job_id": task.task_id,
            "stock_code": task.stock_code,
            "status": task.status,
            "message": "Task submitted. Use `dsa status <job_id>` to check progress.",
        }
        if session:
            result["session_id"] = session
        json_out.ok(result)
    except Exception as e:
        json_out.error("SUBMIT_FAILED", str(e))


@click.group(name="status")
def status() -> None:
    """Check analysis job status."""


@status.command()
@click.argument("job_id")
@pass_json
def job_status(json_out: JsonOutput, job_id: str) -> None:
    """Get the status and progress of an analysis job."""
    from src.services.task_queue import AnalysisTaskQueue

    queue = AnalysisTaskQueue()
    task = queue.get_task(job_id)
    if task is None:
        json_out.error("NOT_FOUND", f"Job {job_id} not found")

    json_out.ok({
        "job_id": task.task_id,
        "stock_code": task.stock_code,
        "status": task.status,
        "progress": task.progress,
        "message": task.message or "",
        "created_at": str(task.created_at) if task.created_at else None,
        "started_at": str(task.started_at) if task.started_at else None,
        "completed_at": str(task.completed_at) if task.completed_at else None,
    })


@click.group(name="result")
def result() -> None:
    """Get analysis job result."""


@result.command()
@click.argument("job_id")
@click.option("--brief", is_flag=True, help="Only return conclusion/score/action")
@click.option("--section", help="Return specific section (news, technical, etc.)")
@click.option("--wait", is_flag=True, help="Wait for job to complete if still running")
@click.option("--wait-timeout", type=int, default=300, help="Max wait time in seconds")
@pass_json
def get_result(
    json_out: JsonOutput,
    job_id: str,
    brief: bool,
    section: Optional[str],
    wait: bool,
    wait_timeout: int,
) -> None:
    """Get the result of a completed analysis job."""
    from src.services.task_queue import AnalysisTaskQueue

    queue = AnalysisTaskQueue()
    task = queue.get_task(job_id)
    if task is None:
        json_out.error("NOT_FOUND", f"Job {job_id} not found")

    # Wait for completion if requested
    if wait and task.status == "PENDING" or task.status == "PROCESSING":
        deadline = time.time() + wait_timeout
        while time.time() < deadline:
            task = queue.get_task(job_id)
            if task.status in ("COMPLETED", "FAILED"):
                break
            time.sleep(2)

    if task.status == "PENDING":
        json_out.ok({
            "job_id": task.task_id,
            "status": "pending",
            "message": "Job is queued, use `dsa status <job_id>` to check progress or `--wait` to block",
        })
    elif task.status == "PROCESSING":
        json_out.ok({
            "job_id": task.task_id,
            "status": "running",
            "progress": task.progress,
            "message": task.message or "Analysis in progress",
        })
    elif task.status == "FAILED":
        json_out.ok({
            "job_id": task.task_id,
            "status": "failed",
            "error": str(task.error) if task.error else "Unknown error",
        })
    elif task.status == "COMPLETED":
        data = {
            "job_id": task.task_id,
            "stock_code": task.stock_code,
            "status": "completed",
        }
        if brief and task.result:
            data["score"] = task.result.get("score")
            data["action"] = task.result.get("action")
            data["summary"] = task.result.get("summary", "")
        elif section and task.result:
            data["section"] = task.result.get(section, {})
        else:
            data["result"] = task.result
        json_out.ok(data)


@click.group(name="cancel")
def cancel() -> None:
    """Cancel a running job."""


@cancel.command()
@click.argument("job_id")
@pass_json
def cancel_job(json_out: JsonOutput, job_id: str) -> None:
    """Cancel a running analysis job."""
    json_out.ok({"job_id": job_id, "status": "cancelled", "message": "Cancellation not yet implemented"})


@click.group(name="jobs")
def jobs() -> None:
    """List active/recent jobs."""


@jobs.command(name="ls")
@click.option("--limit", type=int, default=20, help="Max jobs to show")
@pass_json
def list_jobs(json_out: JsonOutput, limit: int) -> None:
    """List recent analysis jobs."""
    from src.services.task_queue import AnalysisTaskQueue

    queue = AnalysisTaskQueue()
    task_list = queue.list_all_tasks(limit=limit)
    json_out.ok({
        "jobs": [
            {
                "job_id": t.task_id,
                "stock_code": t.stock_code,
                "status": t.status,
                "progress": t.progress,
                "message": t.message or "",
            }
            for t in task_list
        ]
    })
