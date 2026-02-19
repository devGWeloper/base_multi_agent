# Intent 분류 노드 — LLM을 사용하여 사용자 입력의 intent를 분류한다
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from config.intents import Intent
from core.llm import get_llm
from core.logging import get_logger, log_node_execution
from prompts.intent_classifier import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from state import GraphState

logger = get_logger(__name__)


@log_node_execution
def classify_intent(state: GraphState) -> GraphState:
    """사용자의 마지막 메시지를 분석하여 intent를 분류한다."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    user_input = ""
    if last_message is not None:
        user_input = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=USER_PROMPT_TEMPLATE.format(user_input=user_input)),
        ])
        raw_intent = response.content.strip()

        try:
            intent = Intent(raw_intent)
        except ValueError:
            logger.warning(
                "unknown_intent_fallback",
                raw_intent=raw_intent,
                user_input=user_input,
            )
            intent = Intent.UNKNOWN

    except Exception as exc:
        # 예외 발생 시 그래프를 중단시키지 않고 unknown_handler로 라우팅한다
        logger.error("intent_classification_failed", error=str(exc))
        return {
            "intent": Intent.UNKNOWN.value,
            "error": str(exc),
            "messages": [],
            "agent_output": state.get("agent_output", ""),
            "context": state.get("context", []),
            "metadata": state.get("metadata", {}),
        }

    return {
        "intent": intent.value,
        "error": None,
        "messages": [],
        "agent_output": state.get("agent_output", ""),
        "context": state.get("context", []),
        "metadata": state.get("metadata", {}),
    }
