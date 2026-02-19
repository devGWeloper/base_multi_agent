# LLM 인스턴스 생성 및 관리 — 동일 설정으로 중복 생성 방지
from __future__ import annotations

from functools import lru_cache

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
