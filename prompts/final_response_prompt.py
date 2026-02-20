# 최종 응답 생성용 프롬프트 템플릿
from __future__ import annotations

SYSTEM_PROMPT = """\
당신은 최종 응답을 생성하는 어시스턴트입니다.
아래 에이전트 처리 결과와 참고 컨텍스트를 바탕으로 사용자에게 전달할 최종 응답을 작성하세요.

에이전트 처리 결과:
{agent_output}

참고 컨텍스트:
{context}
"""

USER_PROMPT = "위 정보를 바탕으로 사용자에게 전달할 최종 응답을 작성하세요."

FALLBACK_MESSAGE = "죄송합니다, 요청을 처리할 수 없습니다."
