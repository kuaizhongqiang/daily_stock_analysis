"""通知诊断功能已移除（由 AI Agent 接管）"""
import logging
logger = logging.getLogger(__name__)

def check_all_channels(config, verbose=False):
    """通知渠道诊断已移除"""
    logger.info("通知渠道诊断已移除（Agent 模式）")
    return {"status": "disabled", "message": "通知渠道诊断已移除，推送由 AI Agent 接管"}
