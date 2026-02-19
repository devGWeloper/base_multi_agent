"""workflow 통합 테스트 — 실제 그래프 실행, LLM만 mock 처리."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage


def _make_initial_state(user_input: str = "테스트 질문") -> dict:
    return {
        "messages": [HumanMessage(content=user_input)],
        "intent": "",
        "agent_output": "",
        "context": [],
        "metadata": {"session_id": "integration-test"},
        "error": None,
    }


def test_workflow_handles_unknown_intent():
    """LLM이 UNKNOWN을 반환해도 그래프가 종료되고 최종 응답이 생성된다."""
    with (
        patch("nodes.intent_classifier.get_llm") as mock_intent_llm,
        patch("nodes.final_response.get_llm") as mock_final_llm,
    ):
        mock_intent_llm.return_value.invoke.return_value = MagicMock(content="UNKNOWN")
        mock_final_llm.return_value.invoke.return_value = MagicMock(
            content="처리할 수 없는 요청입니다."
        )

        from workflow import build_graph
        g = build_graph()
        result = g.invoke(_make_initial_state("알 수 없는 질문"))

    messages = result.get("messages", [])
    assert len(messages) > 0


def test_workflow_handles_intent_classifier_exception():
    """intent_classifier에서 예외 발생 시 unknown_handler를 통해 정상 응답한다."""
    with (
        patch("nodes.intent_classifier.get_llm") as mock_intent_llm,
        patch("nodes.final_response.get_llm") as mock_final_llm,
    ):
        mock_intent_llm.return_value.invoke.side_effect = Exception("LLM unavailable")
        mock_final_llm.return_value.invoke.return_value = MagicMock(
            content="오류가 발생했습니다."
        )

        from workflow import build_graph
        g = build_graph()
        result = g.invoke(_make_initial_state("질문"))

    # 예외 발생 시 error가 state에 기록되어야 한다
    assert result.get("error") is not None
    # 그래프는 중단되지 않고 최종 응답을 반환해야 한다
    messages = result.get("messages", [])
    assert len(messages) > 0


def test_workflow_unknown_intent_routes_through_unknown_handler():
    """UNKNOWN intent일 때 unknown_handler의 agent_output이 final_response로 전달된다."""
    with (
        patch("nodes.intent_classifier.get_llm") as mock_intent_llm,
        patch("nodes.final_response.get_llm") as mock_final_llm,
    ):
        mock_intent_llm.return_value.invoke.return_value = MagicMock(content="UNKNOWN")
        mock_final_llm.return_value.invoke.return_value = MagicMock(content="최종 응답")

        from workflow import build_graph
        g = build_graph()
        result = g.invoke(_make_initial_state())

    # unknown_handler가 agent_output을 설정했어야 한다
    assert result.get("agent_output") != ""
