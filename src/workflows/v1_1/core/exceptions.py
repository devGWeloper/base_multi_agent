# 커스텀 예외 계층 — 모든 예외는 원인(cause)과 context dict를 함께 전달 가능
from __future__ import annotations

from typing import Any


class MultiAgentBaseError(Exception):
    """프로젝트 공통 베이스 예외."""

    def __init__(
        self,
        message: str = "",
        *,
        cause: Exception | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.cause = cause
        self.context = context or {}
        if cause:
            self.__cause__ = cause


class IntentClassificationError(MultiAgentBaseError):
    """Intent 분류 실패 시 발생."""


class AgentExecutionError(MultiAgentBaseError):
    """Agent 실행 중 오류 발생 시."""


class RAGRetrievalError(MultiAgentBaseError):
    """RAG 검색 실패 시 발생."""


class MCPConnectionError(MultiAgentBaseError):
    """MCP 서버 연결 실패 시 발생."""


class MCPToolError(MultiAgentBaseError):
    """MCP Tool 호출 실패 시 발생."""
