# MCP tool 추상 클래스 — 새 tool 추가 시 이 클래스를 상속
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """모든 MCP tool이 구현해야 하는 인터페이스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """tool 고유 이름."""

    @property
    @abstractmethod
    def description(self) -> str:
        """tool 설명."""

    @property
    @abstractmethod
    def args_schema(self) -> dict[str, Any]:
        """tool 인자 JSON 스키마."""

    @abstractmethod
    def call(self, args: dict[str, Any]) -> dict[str, Any]:
        """tool을 실행하고 결과를 반환한다."""
