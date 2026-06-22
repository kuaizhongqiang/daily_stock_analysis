"""dsa alert — Agent 可注册告警。

Usage:
    dsa alert create --stock 600519 --type price --condition "price < 200"
    dsa alert create --stock 600519 --type volume --condition "volume > 5x_avg"
    dsa alert ls
    dsa alert get <rule_id>
    dsa alert remove <rule_id>
    dsa alert enable <rule_id>
    dsa alert disable <rule_id>
    dsa alert test <rule_id>
"""
from __future__ import annotations

from typing import Optional

import click

from ..output import JsonOutput, pass_json


@click.group(name="alert")
def alert() -> None:
    """Agent 可注册告警。"""


@alert.command()
@click.option("--stock", required=True, help="股票代码，如 600519、AAPL")
@click.option("--type", "alert_type", required=True, help="告警类型: price, volume, price_change, technical")
@click.option("--condition", required=True, help="告警条件描述，如 'price < 200'、'volume > 5x_avg'")
@click.option("--note", help="告警备注")
@pass_json
def create(
    json_out: JsonOutput,
    stock: str,
    alert_type: str,
    condition: str,
    note: Optional[str],
) -> None:
    """创建告警规则。"""
    from src.services.alert_service import AlertService

    payload = {
        "name": note or f"{stock} {alert_type} alert",
        "alert_type": alert_type,
        "stock_code": stock,
        "condition": condition,
        "enabled": True,
    }

    try:
        service = AlertService()
        result = service.create_rule(payload)
        json_out.ok({
            "rule_id": result.get("id"),
            "stock_code": stock,
            "alert_type": alert_type,
            "condition": condition,
            "status": "created",
            "message": f"Alert rule created (id={result.get('id')}). Use `dsa alert test {result.get('id')}` to test.",
        })
    except Exception as e:
        json_out.error("ALERT_CREATE_ERROR", str(e))


@alert.command(name="ls")
@click.option("--stock", help="按股票代码过滤")
@click.option("--enabled", is_flag=True, default=None, help="仅显示启用的告警")
@pass_json
def list_alerts(json_out: JsonOutput, stock: Optional[str], enabled: Optional[bool]) -> None:
    """列出告警规则。"""
    from src.services.alert_service import AlertService

    try:
        service = AlertService()
        rules = service.list_rules(stock_code=stock)
        if enabled:
            rules = [r for r in rules if r.get("enabled")]

        summary = []
        for r in rules:
            summary.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "stock_code": r.get("stock_code"),
                "alert_type": r.get("alert_type"),
                "condition": r.get("condition"),
                "enabled": r.get("enabled", False),
                "created_at": str(r.get("created_at", "")),
            })

        json_out.ok({"alerts": summary, "count": len(summary)})
    except Exception as e:
        json_out.error("ALERT_LIST_ERROR", str(e))


@alert.command()
@click.argument("rule_id", type=int)
@pass_json
def get(json_out: JsonOutput, rule_id: int) -> None:
    """查看告警规则详情。"""
    from src.services.alert_service import AlertService, AlertNotFoundError

    try:
        service = AlertService()
        rule = service.get_rule(rule_id)
        json_out.ok(rule)
    except AlertNotFoundError:
        json_out.error("NOT_FOUND", f"Alert rule {rule_id} not found")
    except Exception as e:
        json_out.error("ALERT_GET_ERROR", str(e))


@alert.command()
@click.argument("rule_id", type=int)
@pass_json
def remove(json_out: JsonOutput, rule_id: int) -> None:
    """删除告警规则。"""
    from src.services.alert_service import AlertService, AlertNotFoundError

    try:
        service = AlertService()
        service.delete_rule(rule_id)
        json_out.ok({
            "rule_id": rule_id,
            "status": "deleted",
        })
    except AlertNotFoundError:
        json_out.error("NOT_FOUND", f"Alert rule {rule_id} not found")
    except Exception as e:
        json_out.error("ALERT_DELETE_ERROR", str(e))


@alert.command()
@click.argument("rule_id", type=int)
@pass_json
def enable(json_out: JsonOutput, rule_id: int) -> None:
    """启用告警规则。"""
    from src.services.alert_service import AlertService, AlertNotFoundError

    try:
        service = AlertService()
        rule = service.enable_rule(rule_id, enabled=True)
        json_out.ok({
            "rule_id": rule_id,
            "enabled": rule.get("enabled"),
            "status": "enabled",
        })
    except AlertNotFoundError:
        json_out.error("NOT_FOUND", f"Alert rule {rule_id} not found")
    except Exception as e:
        json_out.error("ALERT_ENABLE_ERROR", str(e))


@alert.command()
@click.argument("rule_id", type=int)
@pass_json
def disable(json_out: JsonOutput, rule_id: int) -> None:
    """禁用告警规则。"""
    from src.services.alert_service import AlertService, AlertNotFoundError

    try:
        service = AlertService()
        rule = service.enable_rule(rule_id, enabled=False)
        json_out.ok({
            "rule_id": rule_id,
            "enabled": rule.get("enabled"),
            "status": "disabled",
        })
    except AlertNotFoundError:
        json_out.error("NOT_FOUND", f"Alert rule {rule_id} not found")
    except Exception as e:
        json_out.error("ALERT_DISABLE_ERROR", str(e))


@alert.command()
@click.argument("rule_id", type=int)
@pass_json
def test(json_out: JsonOutput, rule_id: int) -> None:
    """测试告警规则是否满足触发条件。"""
    from src.services.alert_service import AlertService, AlertNotFoundError

    try:
        service = AlertService()
        result = service.test_rule(rule_id)
        json_out.ok({
            "rule_id": rule_id,
            "triggered": result.get("triggered", False),
            "current_value": result.get("value"),
            "threshold": result.get("threshold"),
            "details": result.get("details", ""),
        })
    except AlertNotFoundError:
        json_out.error("NOT_FOUND", f"Alert rule {rule_id} not found")
    except Exception as e:
        json_out.error("ALERT_TEST_ERROR", str(e))
