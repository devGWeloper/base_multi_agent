# intent 미매칭 또는 분류 오류 처리 노드
# - error 필드가 있으면 시스템 오류 응답
# - error 필드가 없으면 intent 미매칭 안내 응답
from __future__ import annotations

from config.intents import Intent
from core.logging import get_logger, log_node_execution
from state import GraphState

logger = get_logger(__name__)

_UNKNOWN_MESSAGE = (
    "요청하신 내용을 처리할 수 있는 서비스를 찾지 못했습니다. "
    "다른 방식으로 질문해 주세요."
)
_ERROR_MESSAGE = "요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


@log_node_execution
def handle_unknown(state: GraphState) -> GraphState:
    """intent가 UNKNOWN이거나 분류 오류 발생 시 처리하는 노드."""
    error = state.get("error")

    if error:
        logger.warning("unknown_handler_error_case", error=error)
        agent_output = _ERROR_MESSAGE
    else:
        logger.info("unknown_handler_no_match")
        agent_output = _UNKNOWN_MESSAGE

    return {
        "agent_output": agent_output,
        "messages": [],
        "intent": state.get("intent", Intent.UNKNOWN.value),
        "context": state.get("context", []),
        "metadata": state.get("metadata", {}),
        "error": error,
    }
