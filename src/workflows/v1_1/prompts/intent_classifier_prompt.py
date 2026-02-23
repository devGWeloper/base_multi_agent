# Intent 분류용 프롬프트 템플릿
from __future__ import annotations

from config.intents import Intent

INTENT_LIST = ", ".join(intent.value for intent in Intent)

SYSTEM_PROMPT = f"""\
당신은 사용자 입력의 의도(intent)를 분류하는 분류기입니다.
아래 intent 목록 중 가장 적합한 하나를 반환하세요. 반드시 목록에 있는 값만 반환하세요.

가능한 intent 목록: {INTENT_LIST}

분류할 수 없는 경우 UNKNOWN을 반환하세요.
"""

USER_PROMPT_TEMPLATE = """\
사용자 입력: {user_input}

위 입력에 해당하는 intent를 하나만 반환하세요 (다른 텍스트 없이 intent 값만)."""
