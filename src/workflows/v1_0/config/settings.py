# 환경변수 기반 설정 로딩 (pydantic-settings)
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model_name: str = "gpt-4o-mini"
    openai_temperature: float = 0.0

    milvus_uri: str = "http://localhost:19530"
    milvus_collection_name: str = "default_collection"


@lru_cache
def get_settings() -> Settings:
    return Settings()
