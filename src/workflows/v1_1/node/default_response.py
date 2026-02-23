# 기본 응답 노드 — intent 미매칭 또는 분류 오류 시 처리
# - error 필드가 있으면 시스템 오류 응답 (LLM 호출 없이 고정 메시지)
# - error 필드가 없으면 AgentExecutor를 통해 LLM으로 단순 질의 응답
from __future__ import annotations

from config.intents import Intent
from core.logging import get_logger, log_node_execution
from node._base_agent import BaseAgent
from node._executor import AgentExecutor
from prompt.unknown_handler_prompt import ERROR_MESSAGE, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from state import GraphState

logger = get_logger(__name__)


class DefaultResponseNode(BaseAgent):
    """intent 미매칭 또는 분류 오류를 처리하는 기본 응답 노드."""

    def __init__(self) -> None:
        self._executor = AgentExecutor(
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT_TEMPLATE,
        )

    def run(self, state: GraphState) -> GraphState:
        error = state.get("error")

        if error:
            logger.warning("default_response_error_case", error=error)
            return {
                "agent_output": ERROR_MESSAGE,
                "messages": [],
                "intent": state.get("intent", Intent.UNKNOWN.value),
                "context": state.get("context", []),
                "metadata": state.get("metadata", {}),
                "error": error,
            }

        logger.info("default_response_general_query")
        return self._executor.execute(state)


_node: DefaultResponseNode | None = None


def _get_node() -> DefaultResponseNode:
    global _node
    if _node is None:
        _node = DefaultResponseNode()
    return _node


@log_node_execution
def default_response(state: GraphState) -> GraphState:
    """intent 미매칭 또는 분류 오류 발생 시 기본 응답을 생성한다."""
    return _get_node().run(state)
