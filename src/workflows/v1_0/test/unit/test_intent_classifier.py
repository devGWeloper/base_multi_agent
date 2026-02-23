"""intent_classifier.py 유닛 테스트 — LLM을 mock으로 대체."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from config.intents import Intent
from node.intent_classifier import classify_intent


def test_classify_known_intent(base_state):
    """LLM이 유효한 intent를 반환하면 해당 intent와 error=None을 반환한다."""
    with patch("nodes.intent_classifier.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.return_value = MagicMock(content="INTENT_A")
        result = classify_intent(base_state)

    assert result["intent"] == Intent.INTENT_A.value
    assert result["error"] is None


def test_classify_unknown_on_unrecognized_response(base_state):
    """LLM이 Intent enum에 없는 값을 반환하면 UNKNOWN으로 폴백하고 error는 None이다.

    ValueError는 시스템 오류가 아니라 LLM 응답 파싱 실패이므로 error를 설정하지 않는다.
    """
    with patch("nodes.intent_classifier.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.return_value = MagicMock(content="INVALID_VALUE")
        result = classify_intent(base_state)

    assert result["intent"] == Intent.UNKNOWN.value
    assert result["error"] is None


def test_classify_unknown_on_llm_exception(base_state):
    """LLM 호출 중 예외가 발생하면 UNKNOWN + error가 설정된다 (그래프는 중단되지 않는다)."""
    with patch("nodes.intent_classifier.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.side_effect = Exception("LLM connection error")
        result = classify_intent(base_state)

    assert result["intent"] == Intent.UNKNOWN.value
    assert result["error"] is not None
    assert "LLM connection error" in result["error"]


def test_classify_preserves_existing_context(base_state):
    """분류 결과가 기존 context를 덮어쓰지 않는다."""
    state = {**base_state, "context": ["기존 컨텍스트"]}
    with patch("nodes.intent_classifier.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.return_value = MagicMock(content="INTENT_A")
        result = classify_intent(state)

    assert result["context"] == ["기존 컨텍스트"]
