# Domain Node A 전용 프롬프트 템플릿
from __future__ import annotations

SYSTEM_PROMPT = """\
당신은 INTENT_A 도메인 전문 에이전트입니다.
주어진 컨텍스트와 도구를 활용하여 정확하고 유용한 답변을 생성하세요.

참고 컨텍스트:
{context}
"""

USER_PROMPT_TEMPLATE = """\
사용자 요청: {user_input}

위 요청에 대해 답변하세요."""
