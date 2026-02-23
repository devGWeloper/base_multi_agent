# 최종 응답 생성 노드 — agent_output과 context를 종합하여 최종 응답을 생성한다
from __future__ import annotations

from langchain_core.messages import AIMessage

from core.logging import log_node_execution
from node._base_agent import BaseAgent
from node._executor import AgentExecutor
from prompt.final_response_prompt import FALLBACK_MESSAGE, SYSTEM_PROMPT, USER_PROMPT
from state import GraphState


class FinalResponseNode(BaseAgent):
    """agent_output과 context를 종합하여 최종 응답을 생성하는 노드."""

    def __init__(self) -> None:
        self._executor = AgentExecutor(
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT,
        )

    def run(self, state: GraphState) -> GraphState:
        agent_output = state.get("agent_output", "")
        context_items = state.get("context", [])

        if not agent_output and not context_items:
            return {
                "messages": [AIMessage(content=FALLBACK_MESSAGE)],
                "intent": state.get("intent", ""),
                "agent_output": agent_output,
                "context": context_items,
                "metadata": state.get("metadata", {}),
            }

        result = self._executor.execute(
            state,
            extra_prompt_vars={"agent_output": agent_output},
        )
        return {
            **result,
            "messages": [AIMessage(content=result["agent_output"])],
        }


_node: FinalResponseNode | None = None


def _get_node() -> FinalResponseNode:
    global _node
    if _node is None:
        _node = FinalResponseNode()
    return _node


@log_node_execution
def generate_final_response(state: GraphState) -> GraphState:
    """agent_output과 context를 종합하여 최종 응답을 생성한다."""
    return _get_node().run(state)
