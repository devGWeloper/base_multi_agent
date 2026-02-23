# 조건부 라우팅 함수 — add_conditional_edges에 직접 전달되는 순수 함수
from __future__ import annotations

from config.intents import Intent
from state import GraphState

INTENT_TO_NODE: dict[str, str] = {
    Intent.INTENT_A.value: "agent_a",
    Intent.INTENT_B.value: "agent_b",
    Intent.UNKNOWN.value: "default_response",
}


def route_by_intent(state: GraphState) -> str:
    """state의 intent 값을 보고 다음 노드 이름을 반환한다."""
    intent = state.get("intent", Intent.UNKNOWN.value)
    return INTENT_TO_NODE.get(intent, "default_response")
