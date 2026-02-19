# 로컬 개발/테스트용 실행 진입점
from __future__ import annotations

from langchain_core.messages import HumanMessage

from workflow import graph


def main() -> None:
    user_input = input("질문을 입력하세요: ")

    result = graph.invoke({
        "messages": [HumanMessage(content=user_input)],
        "intent": "",
        "agent_output": "",
        "context": [],
        "metadata": {"session_id": "local-test"},
        "error": None,
    })

    final_messages = result.get("messages", [])
    if final_messages:
        last = final_messages[-1]
        content = last.content if hasattr(last, "content") else str(last)
        print(f"\n[응답]\n{content}")
    else:
        print("\n[응답 없음]")


if __name__ == "__main__":
    main()
