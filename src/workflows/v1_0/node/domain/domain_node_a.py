# Domain Agent A (intent: INTENT_A) — 추후 비즈니스 로직을 채워넣을 자리
from __future__ import annotations

from core.logging import get_logger, log_node_execution
from mcp.client import MCPClient
from mcp.tool.search_tool import SearchTool
from node._base_agent import BaseAgent
from node._executor import AgentExecutor
from prompt.agent.agent_a_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from rag.iflow_retriever import IflowRetriever
from state import GraphState

logger = get_logger(__name__)


class AgentA(BaseAgent):
    """INTENT_A intent 처리 Agent — retriever + tool 조합을 주입받는다."""

    def __init__(self) -> None:
        # TODO: 도메인에 맞는 retriever/tool 조합으로 교체
        mcp_client = MCPClient()
        mcp_client.register_tool(SearchTool())

        self._executor = AgentExecutor(
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT_TEMPLATE,
            retrievers=[IflowRetriever()],
            mcp_client=mcp_client,
            tools=["search"],
        )

    def run(self, state: GraphState) -> GraphState:
        return self._executor.execute(state)


_agent: AgentA | None = None


def _get_agent() -> AgentA:
    # 모듈 임포트 시점이 아니라 첫 호출 시점에 초기화한다.
    # Milvus / MCP 등 외부 의존성이 없어도 import가 성공한다.
    global _agent
    if _agent is None:
        _agent = AgentA()
    return _agent


@log_node_execution
def agent_a_node(state: GraphState) -> GraphState:
    """LangGraph 노드 함수로 Agent A를 실행한다."""
    return _get_agent().run(state)
