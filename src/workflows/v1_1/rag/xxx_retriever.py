# 추가 소스 retriever 구현체 예시 (pymilvus 기반)
from __future__ import annotations

from pymilvus import MilvusClient

from config.settings import get_settings
from core.exceptions import RAGRetrievalError
from core.logging import get_logger
from rag.base_retriever import BaseRetriever, Document

logger = get_logger(__name__)


class XxxRetriever(BaseRetriever):
    """추가 데이터 소스를 Milvus에서 검색하는 retriever 예시."""

    def __init__(self, collection_name: str | None = None) -> None:
        settings = get_settings()
        self._uri = settings.milvus_uri
        self._collection = collection_name or settings.milvus_collection_name
        self._client: MilvusClient | None = None

    def _get_client(self) -> MilvusClient:
        if self._client is None:
            try:
                self._client = MilvusClient(uri=self._uri)
            except Exception as exc:
                raise RAGRetrievalError(
                    f"Milvus 연결 실패: {self._uri}",
                    cause=exc,
                    context={"uri": self._uri},
                ) from exc
        return self._client

    def retrieve(self, query: str) -> list[Document]:
        """query 문자열을 임베딩하여 Milvus에서 유사 문서를 검색한다."""
        logger.info("xxx_retrieve_start", query=query, collection=self._collection)
        try:
            client = self._get_client()

            # TODO: Step 1 — query를 벡터로 변환한다. (iflow_retriever.py 참고)

            # TODO: Step 2 — Milvus 벡터 검색을 수행한다. (iflow_retriever.py 참고)
            #   이 retriever가 조회할 collection은 생성자 인자로 주입한다.
            #   예) XxxRetriever(collection_name="my_domain_collection")

            _ = client  # placeholder — Step 1·2 구현 후 제거
            logger.info("xxx_retrieve_end", query=query, results_count=0)
            return []
        except RAGRetrievalError:
            raise
        except Exception as exc:
            raise RAGRetrievalError(
                "xxx 검색 중 오류 발생",
                cause=exc,
                context={"query": query, "collection": self._collection},
            ) from exc
