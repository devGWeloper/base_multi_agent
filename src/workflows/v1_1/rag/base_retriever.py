# RAG retriever 추상 베이스 클래스 — 새 retriever 추가 시 이 클래스를 상속
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Document:
    """검색된 문서 한 건을 표현한다."""

    page_content: str = ""
    metadata: dict = field(default_factory=dict)


class BaseRetriever(ABC):
    """모든 RAG retriever가 구현해야 하는 인터페이스."""

    @abstractmethod
    def retrieve(self, query: str) -> list[Document]:
        """쿼리 문자열로 관련 문서를 검색하여 반환한다."""
