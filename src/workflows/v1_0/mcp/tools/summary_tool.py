# 예시 MCP tool: 요약 — 실제 MCP tool 연동 로직은 추후 구현
from __future__ import annotations

from typing import Any

from mcp.tools.base_tool import BaseTool


class SummaryTool(BaseTool):
    """텍스트를 요약하는 MCP tool stub."""

    @property
    def name(self) -> str:
        return "summary"

    @property
    def description(self) -> str:
        return "주어진 텍스트를 요약한다."

    @property
    def args_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "요약할 텍스트"},
            },
            "required": ["text"],
        }

    def call(self, args: dict[str, Any]) -> dict[str, Any]:
        # TODO: 실제 요약 로직 구현
        text = args.get("text", "")
        return {"summary": text[:100], "message": "stub: 요약 결과"}
