# intent 미매칭 또는 분류 오류 처리 노드
# - error 필드가 있으면 시스템 오류 응답 (LLM 호출 없이 고정 메시지)
# - error 필드가 없으면 AgentExecutor를 통해 LLM으로 단순 질의 응답
from __future__ import annotations

from config.intents import Intent
from core.logging import get_logger, log_node_execution
from node.base_agent import BaseAgent
from node.executor import AgentExecutor
from prompt.unknown_handler_prompt import ERROR_MESSAGE, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from state import GraphState

logger = get_logger(__name__)


class UnknownHandlerNode(BaseAgent):
    """UNKNOWN intent 또는 분류 오류를 처리하는 노드."""

    def __init__(self) -> None:
        self._executor = AgentExecutor(
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT_TEMPLATE,
        )

    def run(self, state: GraphState) -> GraphState:
        error = state.get("error")

        if error:
            logger.warning("unknown_handler_error_case", error=error)
            return {
                "agent_output": ERROR_MESSAGE,
                "messages": [],
                "intent": state.get("intent", Intent.UNKNOWN.value),
                "context": state.get("context", []),
                "metadata": state.get("metadata", {}),
                "error": error,
            }

        logger.info("unknown_handler_general_query")
        return self._executor.execute(state)


_node: UnknownHandlerNode | None = None


def _get_node() -> UnknownHandlerNode:
    global _node
    if _node is None:
        _node = UnknownHandlerNode()
    return _node


@log_node_execution
def handle_unknown(state: GraphState) -> GraphState:
    """intent가 UNKNOWN이거나 분류 오류 발생 시 처리하는 노드."""
    return _get_node().run(state)
