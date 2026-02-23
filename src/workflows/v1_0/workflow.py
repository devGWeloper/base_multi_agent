# GAIA 플랫폼 고정 진입점 — StateGraph 정의, 노드/엣지 등록, compile
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from node.default_response import default_response
from node.domain.domain_node_a import agent_a_node
from node.domain.domain_node_b import agent_b_node
from node.final_response import generate_final_response
from node.intent_classifier import classify_intent
from node.router import route_by_intent
from state import GraphState


def build_graph() -> StateGraph:
    sg = StateGraph(GraphState)

    sg.add_node("intent_classifier", classify_intent)
    sg.add_node("agent_a", agent_a_node)
    sg.add_node("agent_b", agent_b_node)
    sg.add_node("default_response", default_response)
    sg.add_node("final_response", generate_final_response)

    sg.add_edge(START, "intent_classifier")
    sg.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "agent_a": "agent_a",
            "agent_b": "agent_b",
            "default_response": "default_response",
        },
    )
    sg.add_edge("agent_a", "final_response")
    sg.add_edge("agent_b", "final_response")
    sg.add_edge("default_response", "final_response")
    sg.add_edge("final_response", END)

    return sg.compile()


graph = build_graph()
