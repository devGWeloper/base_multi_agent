# 그래프 전체에서 공유하는 State 정의
# 추후 GAIA SDK 도입 시: class GraphState(GaiaGraphState)로 교체
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class GraphState(TypedDict):
    messages: Annotated[list, operator.add]
    intent: str
    agent_output: str
    context: list[str]
    metadata: dict[str, Any]
    error: str | None  # 시스템 오류 발생 시 설정; unknown_handler에서 오류/미매칭 구분에 사용
