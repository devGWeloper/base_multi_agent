# intent 미매칭 또는 분류 오류 처리 노드
# - error 필드가 있으면 시스템 오류 응답
# - error 필드가 없으면 LLM으로 단순 질의 응답
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from config.intents import Intent
from core.llm import call_llm
from core.logging import get_logger, log_node_execution
from prompts.unknown_handler_prompt import ERROR_MESSAGE, SYSTEM_PROMPT
from state import GraphState

logger = get_logger(__name__)


@log_node_execution
def handle_unknown(state: GraphState) -> GraphState:
    """intent가 UNKNOWN이거나 분류 오류 발생 시 처리하는 노드.

    - error가 있으면 시스템 오류 안내 메시지를 반환한다.
    - error가 없으면 단순 질의로 판단하고 LLM으로 직접 답변한다.
    """
    error = state.get("error")

    if error:
        logger.warning("unknown_handler_error_case", error=error)
        agent_output = ERROR_MESSAGE
    else:
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        user_input = (
            last_message.content
            if last_message and hasattr(last_message, "content")
            else str(last_message) if last_message else ""
        )
        logger.info("unknown_handler_general_query", user_input=user_input)
        response = call_llm([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ])
        agent_output = response.content

    return {
        "agent_output": agent_output,
        "messages": [],
        "intent": state.get("intent", Intent.UNKNOWN.value),
        "context": state.get("context", []),
        "metadata": state.get("metadata", {}),
        "error": error,
    }
