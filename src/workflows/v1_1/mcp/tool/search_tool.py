# 예시 MCP tool: 검색 — 실제 MCP tool 연동 로직은 추후 구현
from __future__ import annotations

from typing import Any

from mcp.tool.base_tool import BaseTool


class SearchTool(BaseTool):
    """외부 검색 API를 호출하는 MCP tool stub."""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "외부 소스에서 키워드 기반 검색을 수행한다."

    @property
    def args_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 쿼리"},
            },
            "required": ["query"],
        }

    def call(self, args: dict[str, Any]) -> dict[str, Any]:
        # TODO: 실제 검색 API 연동 구현
        query = args.get("query", "")
        return {"results": [], "query": query, "message": "stub: 검색 결과 없음"}
