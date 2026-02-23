"""router.py 유닛 테스트 — 외부 의존성 없는 순수 함수 테스트."""
from __future__ import annotations

import pytest

from config.intents import Intent
from nodes.router import route_by_intent


def test_route_intent_a(base_state):
    result = route_by_intent({**base_state, "intent": Intent.INTENT_A.value})
    assert result == "agent_a"


def test_route_intent_b(base_state):
    result = route_by_intent({**base_state, "intent": Intent.INTENT_B.value})
    assert result == "agent_b"


def test_route_unknown(base_state):
    result = route_by_intent({**base_state, "intent": Intent.UNKNOWN.value})
    assert result == "unknown_handler"


def test_route_unregistered_intent_falls_back_to_unknown_handler(base_state):
    """INTENT_TO_NODE에 없는 intent는 unknown_handler로 폴백된다."""
    result = route_by_intent({**base_state, "intent": "NOT_REGISTERED"})
    assert result == "unknown_handler"


def test_route_empty_intent_falls_back_to_unknown_handler(base_state):
    """intent가 빈 문자열이면 unknown_handler로 폴백된다."""
    result = route_by_intent({**base_state, "intent": ""})
    assert result == "unknown_handler"
