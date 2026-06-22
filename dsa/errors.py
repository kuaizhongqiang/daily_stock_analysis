"""
统一错误码定义 — CLI / MCP / REST API 三层共享。

确保 Agent 通过任意接口层调用时，都能以一致的格式处理错误。

## 错误响应格式

### CLI / MCP
```json
{
  "status": "error",
  "error": {"code": "NOT_FOUND", "message": "...", "retryable": false}
}
```

### REST API
```json
{
  "error": "NOT_FOUND",
  "message": "...",
  "retryable": false
}
```
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    """统一错误码枚举。"""

    # ==== 通用错误 (4xx) ====
    VALIDATION_ERROR = "VALIDATION_ERROR"        # 参数校验失败
    NOT_FOUND = "NOT_FOUND"                      # 资源不存在
    DUPLICATE_TASK = "DUPLICATE_TASK"            # 重复提交
    OPERATION_REJECTED = "OPERATION_REJECTED"     # 操作被拒绝（审批流）
    APPROVAL_TIMEOUT = "APPROVAL_TIMEOUT"         # 审批超时
    RATE_LIMITED = "RATE_LIMITED"                # 请求频率限制

    # ==== 服务端错误 (5xx) ====
    INTERNAL_ERROR = "INTERNAL_ERROR"            # 内部错误
    ANALYSIS_FAILED = "ANALYSIS_FAILED"           # 分析过程失败
    UPSTREAM_ERROR = "UPSTREAM_ERROR"             # 上游服务（数据源/LLM）错误
    TIMEOUT = "TIMEOUT"                          # 请求超时
    CONNECTION_FAILED = "CONNECTION_FAILED"       # 连接失败
    MCP_SDK_MISSING = "MCP_SDK_MISSING"          # MCP SDK 未安装

    # ==== 数据源错误 ====
    DATA_SOURCE_UNAVAILABLE = "DATA_SOURCE_UNAVAILABLE"
    DATA_SOURCE_NOT_CONFIGURED = "DATA_SOURCE_NOT_CONFIGURED"

    # ==== 配置错误 ====
    CONFIG_MISSING = "CONFIG_MISSING"            # 必需配置缺失
    CONFIG_INVALID = "CONFIG_INVALID"             # 配置值无效


# 非重试性错误（客户端问题，重试无意义）
NON_RETRYABLE_CODES = {
    ErrorCode.VALIDATION_ERROR,
    ErrorCode.NOT_FOUND,
    ErrorCode.OPERATION_REJECTED,
    ErrorCode.APPROVAL_TIMEOUT,
    ErrorCode.DATA_SOURCE_NOT_CONFIGURED,
    ErrorCode.CONFIG_MISSING,
    ErrorCode.CONFIG_INVALID,
    ErrorCode.DUPLICATE_TASK,
    ErrorCode.MCP_SDK_MISSING,
}


def is_retryable(code: ErrorCode) -> bool:
    """判断错误是否可重试。"""
    return code not in NON_RETRYABLE_CODES


def error_dict(
    code: ErrorCode | str,
    message: str,
    *,
    retryable: Optional[bool] = None,
    detail: Any = None,
) -> dict[str, Any]:
    """构建统一错误字典。

    Args:
        code: 错误码（ErrorCode 枚举或字符串）
        message: 人类可读的错误描述
        retryable: 是否可重试，None 时根据 code 自动推断
        detail: 附加调试信息（仅 API 层使用）

    Returns:
        统一格式的错误字典
    """
    code_str = code.value if isinstance(code, ErrorCode) else code
    if retryable is None:
        retryable = is_retryable(code) if isinstance(code, ErrorCode) else False
    return {
        "code": code_str,
        "message": message,
        "retryable": retryable,
    }
