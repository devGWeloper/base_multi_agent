# Domain Agent B (intent: INTENT_B) — 추후 비즈니스 로직을 채워넣을 자리
from __future__ import annotations

from core.logging import get_logger, log_node_execution
from mcp.client import MCPClient
from mcp.tools.summary_tool import SummaryTool
from nodes.agents.base_agent import BaseAgent
from nodes.agents.executor import AgentExecutor
from prompts.agents.agent_b_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from rag.xxx_retriever import XxxRetriever
from state import GraphState

logger = get_logger(__name__)


class AgentB(BaseAgent):
    """INTENT_B intent 처리 Agent — retriever + tool 조합을 주입받는다."""

    def __init__(self) -> None:
        # TODO: 도메인에 맞는 retriever/tool 조합으로 교체
        mcp_client = MCPClient()
        mcp_client.register_tool(SummaryTool())

        self._executor = AgentExecutor(
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT_TEMPLATE,
            retrievers=[XxxRetriever()],
            mcp_client=mcp_client,
            tools=["summary"],
        )

    def run(self, state: GraphState) -> GraphState:
        return self._executor.execute(state)


_agent: AgentB | None = None


def _get_agent() -> AgentB:
    # 모듈 임포트 시점이 아니라 첫 호출 시점에 초기화한다.
    # Milvus / MCP 등 외부 의존성이 없어도 import가 성공한다.
    global _agent
    if _agent is None:
        _agent = AgentB()
    return _agent


@log_node_execution
def agent_b_node(state: GraphState) -> GraphState:
    """LangGraph 노드 함수로 Agent B를 실행한다."""
    return _get_agent().run(state)
