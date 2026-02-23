# Agent 추상 클래스 — 인터페이스 정의만 담당, 실행 로직은 executor.py에 위임
from __future__ import annotations

from abc import ABC, abstractmethod

from state import GraphState


class BaseAgent(ABC):
    """모든 도메인 Agent가 구현해야 하는 인터페이스."""

    @abstractmethod
    def run(self, state: GraphState) -> GraphState:
        """state를 받아 처리한 뒤 갱신된 state를 반환한다."""
