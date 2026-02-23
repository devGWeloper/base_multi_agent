"""unknown_handler.py 유닛 테스트 — 외부 의존성 없는 순수 함수 테스트."""
from __future__ import annotations

import pytest

from config.intents import Intent
from node.default_response import default_response


def test_returns_guidance_message_when_no_error(base_state):
    """error 없이 UNKNOWN intent가 들어오면 미매칭 안내 메시지를 agent_output으로 반환한다."""
    state = {**base_state, "intent": Intent.UNKNOWN.value, "error": None}
    result = default_response(state)

    assert result["agent_output"] != ""
    assert result["intent"] == Intent.UNKNOWN.value
    assert result["error"] is None


def test_returns_error_message_when_error_set(base_state):
    """error가 있으면 시스템 오류 메시지를 agent_output으로 반환한다."""
    state = {**base_state, "intent": Intent.UNKNOWN.value, "error": "LLM connection error"}
    result = default_response(state)

    assert result["agent_output"] != ""
    assert result["error"] == "LLM connection error"


def test_error_and_no_error_produce_different_messages(base_state):
    """시스템 오류 케이스와 미매칭 케이스는 서로 다른 메시지를 반환한다."""
    no_error_state = {**base_state, "intent": Intent.UNKNOWN.value, "error": None}
    error_state = {**base_state, "intent": Intent.UNKNOWN.value, "error": "some error"}

    result_no_error = default_response(no_error_state)
    result_error = default_response(error_state)

    assert result_no_error["agent_output"] != result_error["agent_output"]


def test_preserves_metadata(base_state):
    """metadata가 변경 없이 그대로 전달된다."""
    state = {**base_state, "intent": Intent.UNKNOWN.value, "error": None}
    result = default_response(state)

    assert result["metadata"] == base_state["metadata"]


def test_returns_empty_messages(base_state):
    """messages 누적을 막기 위해 빈 리스트를 반환한다."""
    state = {**base_state, "intent": Intent.UNKNOWN.value, "error": None}
    result = default_response(state)

    assert result["messages"] == []
