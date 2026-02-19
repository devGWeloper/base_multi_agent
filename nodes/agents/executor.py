# Agent 공통 실행 로직 — RAG 조회, MCP tool 호출, LLM 호출을 조율한다
from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from core.exceptions import AgentExecutionError
from core.llm import get_llm
from core.logging import get_logger
from mcp.client import MCPClient
from prompts.agent_base import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from rag.base_retriever import BaseRetriever
from state import GraphState

logger = get_logger(__name__)


class AgentExecutor:
    """주입된 retriever/tool 조합으로 Agent 실행을 조율한다."""

    def __init__(
        self,
        retrievers: list[BaseRetriever] | None = None,
        mcp_client: MCPClient | None = None,
        tools: list[str] | None = None,
    ) -> None:
        self._retrievers = retrievers or []
        self._mcp_client = mcp_client
        self._tools = tools or []

    def execute(self, state: GraphState) -> GraphState:
        """RAG 조회 → MCP tool 호출 → LLM 호출 순서로 실행한다."""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        user_input = (
            last_message.content
            if last_message and hasattr(last_message, "content")
            else str(last_message) if last_message else ""
        )

        context_items: list[str] = list(state.get("context", []))

        try:
            context_items = self._run_retrieval(user_input, context_items)
            tool_results = self._run_tools(user_input)
            agent_output = self._run_llm(user_input, context_items, tool_results)
        except AgentExecutionError:
            raise
        except Exception as exc:
            raise AgentExecutionError(
                "Agent 실행 중 오류 발생",
                cause=exc,
                context={"user_input": user_input},
            ) from exc

        return {
            "messages": [],
            "intent": state.get("intent", ""),
            "agent_output": agent_output,
            "context": context_items,
            "metadata": state.get("metadata", {}),
        }

    def _run_retrieval(
        self, query: str, context_items: list[str]
    ) -> list[str]:
        """주입된 모든 retriever로 RAG 조회를 수행한다."""
        for retriever in self._retrievers:
            logger.info("retrieval_start", retriever=type(retriever).__name__)
            try:
                docs = retriever.retrieve(query)
                context_items.extend(doc.page_content for doc in docs)
            except Exception as exc:
                raise AgentExecutionError(
                    f"RAG 조회 실패: {type(retriever).__name__}",
                    cause=exc,
                    context={"retriever": type(retriever).__name__, "query": query},
                ) from exc
        return context_items

    def _run_tools(self, user_input: str) -> list[dict[str, Any]]:
        """주입된 MCP client를 통해 등록된 tool들을 호출한다.

        현재는 등록된 tool을 순서대로 모두 호출하는 단순 파이프라인 방식이다.

        TODO: 아래 중 하나로 교체하면 진짜 '에이전트' 동작이 된다.
          - LLM tool calling 루프: LLM이 tool 선택 + args 생성 → 결과를 다시 LLM에 전달
            (langchain: create_tool_calling_agent + AgentExecutor,
             또는 직접 while 루프로 AIMessage.tool_calls 처리)
          - ReAct 패턴: Reasoning → Action → Observation 반복
            (langgraph: ToolNode + should_continue 조건 엣지 조합)
        """
        results: list[dict[str, Any]] = []
        if not self._mcp_client or not self._tools:
            return results

        for tool_name in self._tools:
            logger.info("tool_call_start", tool_name=tool_name)
            try:
                result = self._mcp_client.call_tool(tool_name, {"query": user_input})
                results.append(result)
            except Exception as exc:
                raise AgentExecutionError(
                    f"MCP tool 호출 실패: {tool_name}",
                    cause=exc,
                    context={"tool_name": tool_name, "user_input": user_input},
                ) from exc
        return results

    def _run_llm(
        self,
        user_input: str,
        context_items: list[str],
        tool_results: list[dict[str, Any]],
    ) -> str:
        """수집된 컨텍스트와 tool 결과를 바탕으로 LLM 호출을 수행한다."""
        context_text = "\n".join(context_items) if context_items else "없음"
        if tool_results:
            context_text += "\n\n[Tool 결과]\n" + "\n".join(
                str(r) for r in tool_results
            )

        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT.format(context=context_text)),
            HumanMessage(content=USER_PROMPT_TEMPLATE.format(user_input=user_input)),
        ])
        return response.content
