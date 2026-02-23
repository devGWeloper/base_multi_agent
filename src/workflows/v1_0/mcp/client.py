# MCP 단일 서버 연결 클라이언트 — 실제 MCP 서버 연결은 추후 구현
from __future__ import annotations

from typing import Any

from core.exceptions import MCPConnectionError, MCPToolError
from core.logging import get_logger
from mcp.tools.base_tool import BaseTool

logger = get_logger(__name__)


class MCPClient:
    """MCP 서버에 연결하여 tool을 관리하고 호출하는 클라이언트."""

    def __init__(self, server_url: str = "") -> None:
        self._server_url = server_url
        self._tools: dict[str, BaseTool] = {}
        self._connected = False

    def connect(self) -> None:
        """MCP 서버에 연결한다."""
        # TODO: 실제 MCP 서버 연결 로직 구현
        logger.info("mcp_connect", server_url=self._server_url)
        try:
            self._connected = True
        except Exception as exc:
            raise MCPConnectionError(
                f"MCP 서버 연결 실패: {self._server_url}",
                cause=exc,
                context={"server_url": self._server_url},
            ) from exc

    def register_tool(self, tool: BaseTool) -> None:
        """tool을 클라이언트에 등록한다."""
        self._tools[tool.name] = tool
        logger.info("mcp_tool_registered", tool_name=tool.name)

    def get_tool(self, tool_name: str) -> BaseTool:
        """이름으로 등록된 tool을 조회한다."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise MCPToolError(
                f"등록되지 않은 tool: {tool_name}",
                context={"tool_name": tool_name, "available": list(self._tools.keys())},
            )
        return tool

    def call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """등록된 tool을 이름으로 찾아 호출한다."""
        logger.info("mcp_tool_call_start", tool_name=tool_name, args=args)
        tool = self.get_tool(tool_name)
        try:
            result = tool.call(args)
            logger.info("mcp_tool_call_end", tool_name=tool_name)
            return result
        except MCPToolError:
            raise
        except Exception as exc:
            raise MCPToolError(
                f"Tool 호출 실패: {tool_name}",
                cause=exc,
                context={"tool_name": tool_name, "args": args},
            ) from exc

    @property
    def available_tools(self) -> list[str]:
        return list(self._tools.keys())
