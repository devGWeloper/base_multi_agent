# 사내 iflow 블로그 소스 retriever 구현체 (pymilvus 기반)
from __future__ import annotations

from pymilvus import MilvusClient

from config.settings import get_settings
from core.exceptions import RAGRetrievalError
from core.logging import get_logger
from rag.base_retriever import BaseRetriever, Document

logger = get_logger(__name__)


class IflowRetriever(BaseRetriever):
    """iflow 블로그 데이터를 Milvus에서 검색하는 retriever.

    각 Agent는 자신이 조회할 collection을 생성자 인자로 지정한다.
    지정하지 않으면 settings.milvus_collection_name(기본값)을 사용한다.

    Agent 생성자 예시:
        AgentExecutor(retrievers=[IflowRetriever(collection_name="iflow_blog")])
    """

    def __init__(self, collection_name: str | None = None) -> None:
        settings = get_settings()
        self._uri = settings.milvus_uri
        # TODO: Agent별로 다른 collection을 사용할 경우 collection_name 인자로 전달한다.
        #       예) IflowRetriever(collection_name="iflow_blog_v2")
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
        logger.info("iflow_retrieve_start", query=query, collection=self._collection)
        try:
            client = self._get_client()

            # TODO: Step 1 — query를 벡터로 변환한다.
            #   임베딩 모델은 팀 표준에 맞게 선택한다.
            #   예) OpenAI:
            #       from openai import OpenAI
            #       vector = OpenAI().embeddings.create(
            #           model="text-embedding-3-small", input=query
            #       ).data[0].embedding
            #   예) HuggingFace:
            #       from sentence_transformers import SentenceTransformer
            #       vector = SentenceTransformer("...").encode(query).tolist()

            # TODO: Step 2 — Milvus 벡터 검색을 수행한다.
            #   search_params와 output_fields는 collection 스키마에 맞게 조정한다.
            #   예)
            #       results = client.search(
            #           collection_name=self._collection,
            #           data=[vector],
            #           limit=5,
            #           search_params={"metric_type": "IP", "params": {}},
            #           output_fields=["content", "source"],
            #       )
            #       return [
            #           Document(
            #               page_content=hit["entity"]["content"],
            #               metadata={"source": hit["entity"]["source"], "score": hit["distance"]},
            #           )
            #           for hit in results[0]
            #       ]

            _ = client  # placeholder — Step 1·2 구현 후 제거
            logger.info("iflow_retrieve_end", query=query, results_count=0)
            return []
        except RAGRetrievalError:
            raise
        except Exception as exc:
            raise RAGRetrievalError(
                "iflow 검색 중 오류 발생",
                cause=exc,
                context={"query": query, "collection": self._collection},
            ) from exc
