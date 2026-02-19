# 최종 응답 생성 노드 — agent_output과 context를 종합하여 최종 응답을 생성한다
from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.llm import get_llm
from core.logging import log_node_execution
from state import GraphState


@log_node_execution
def generate_final_response(state: GraphState) -> GraphState:
    """agent_output과 context를 종합하여 최종 응답을 생성한다."""
    agent_output = state.get("agent_output", "")
    context_items = state.get("context", [])
    messages = state.get("messages", [])

    if not agent_output and not context_items:
        return {
            "messages": [AIMessage(content="죄송합니다, 요청을 처리할 수 없습니다.")],
            "intent": state.get("intent", ""),
            "agent_output": agent_output,
            "context": context_items,
            "metadata": state.get("metadata", {}),
        }

    context_text = "\n".join(context_items) if context_items else "없음"

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(
            content=(
                "당신은 최종 응답을 생성하는 어시스턴트입니다.\n"
                "아래 에이전트 처리 결과와 참고 컨텍스트를 바탕으로 "
                "사용자에게 전달할 최종 응답을 작성하세요.\n\n"
                f"에이전트 처리 결과:\n{agent_output}\n\n"
                f"참고 컨텍스트:\n{context_text}"
            ),
        ),
        HumanMessage(
            content="위 정보를 바탕으로 사용자에게 전달할 최종 응답을 작성하세요.",
        ),
    ])

    return {
        "messages": [AIMessage(content=response.content)],
        "intent": state.get("intent", ""),
        "agent_output": agent_output,
        "context": context_items,
        "metadata": state.get("metadata", {}),
    }
