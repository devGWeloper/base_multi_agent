# LLM 인스턴스 생성 및 관리 — 동일 설정으로 중복 생성 방지
from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from config.settings import get_settings


@lru_cache
def get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model_name,
        temperature=settings.openai_temperature,
    )


def call_llm(
    messages: list[BaseMessage],
    tools: list[Any] | None = None,
) -> BaseMessage:
    """LLM을 호출하고 응답 메시지를 반환한다.

    Args:
        messages: LLM에 전달할 메시지 목록.
        tools: bind_tools에 전달할 tool 목록. None이면 tool 없이 호출한다.

    Returns:
        LLM 응답 BaseMessage.
    """
    llm: BaseChatModel = get_llm()
    if tools:
        llm = llm.bind_tools(tools)
    return llm.invoke(messages)
