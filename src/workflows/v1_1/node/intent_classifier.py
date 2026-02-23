# Intent 분류 노드 — LLM을 사용하여 사용자 입력의 intent를 분류한다
from __future__ import annotations

from config.intents import Intent
from core.exceptions import AgentExecutionError
from core.logging import get_logger, log_node_execution
from node._base_agent import BaseAgent
from node._executor import AgentExecutor
from prompt.intent_classifier_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from state import GraphState

logger = get_logger(__name__)


class IntentClassifierNode(BaseAgent):
    """사용자 입력의 intent를 분류하는 노드."""

    def __init__(self) -> None:
        self._executor = AgentExecutor(
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT_TEMPLATE,
        )

    def run(self, state: GraphState) -> GraphState:
        try:
            result = self._executor.execute(state)
            raw_intent = result["agent_output"].strip()

            try:
                intent = Intent(raw_intent)
            except ValueError:
                logger.warning(
                    "unknown_intent_fallback",
                    raw_intent=raw_intent,
                )
                intent = Intent.UNKNOWN

            return {
                "intent": intent.value,
                "error": None,
                "messages": [],
                "agent_output": state.get("agent_output", ""),
                "context": result.get("context", []),
                "metadata": state.get("metadata", {}),
            }

        except (AgentExecutionError, Exception) as exc:
            logger.error("intent_classification_failed", error=str(exc))
            return {
                "intent": Intent.UNKNOWN.value,
                "error": str(exc),
                "messages": [],
                "agent_output": state.get("agent_output", ""),
                "context": state.get("context", []),
                "metadata": state.get("metadata", {}),
            }


_node: IntentClassifierNode | None = None


def _get_node() -> IntentClassifierNode:
    global _node
    if _node is None:
        _node = IntentClassifierNode()
    return _node


@log_node_execution
def classify_intent(state: GraphState) -> GraphState:
    """사용자의 마지막 메시지를 분석하여 intent를 분류한다."""
    return _get_node().run(state)
