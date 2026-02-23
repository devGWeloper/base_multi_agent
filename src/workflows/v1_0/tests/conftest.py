from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from state import GraphState


@pytest.fixture
def base_state() -> GraphState:
    """모든 테스트에서 공통으로 사용하는 초기 GraphState."""
    return {
        "messages": [HumanMessage(content="테스트 질문입니다")],
        "intent": "",
        "agent_output": "",
        "context": [],
        "metadata": {"session_id": "test-session"},
        "error": None,
    }
