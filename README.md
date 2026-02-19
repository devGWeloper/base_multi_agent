# Multi-Agent Base Project

LangGraph + LangChain 기반 Multi-Agent 아키텍처 골격 프로젝트.
GAIA 플랫폼 위에서 동작하며, 도메인별 비즈니스 로직을 채워넣을 수 있는 구조를 제공한다.

---

## 아키텍처

### 전체 흐름

```
User Input
  → Intent Classifier (LLM으로 intent 분류)
  → Router (conditional_edges — intent 값으로 다음 노드 결정)
  ┌─→ Agent A ──→ Final Response ──→ END
  ├─→ Agent B ──→ Final Response ──→ END
  └─→ Unknown Handler ──→ Final Response ──→ END
```

- **Intent Classifier** — 사용자 입력을 LLM으로 분석하여 `Intent` enum 값 중 하나로 분류한다. 분류 실패 시 예외를 발생시키지 않고 `state.error`에 원인을 기록한 뒤 `UNKNOWN`으로 fallback한다.
- **Router** — `intent_classifier` 노드의 conditional edge 함수. `state.intent` 값을 보고 다음 노드 이름을 반환하는 순수 함수이다 (별도 노드가 아님).
- **Domain Agent** — 각 intent별 처리를 담당한다. Agent 생성 시 사용할 RAG retriever와 MCP tool을 **선택적으로 주입**받으며, 공통 실행 로직(`executor.py`)에 위임한다.
- **Unknown Handler** — `UNKNOWN` intent 또는 분류 오류를 처리하는 전용 노드. `state.error` 유무로 시스템 오류와 단순 미매칭을 구분한다.
- **Final Response** — agent 처리 결과(`agent_output`)와 RAG 컨텍스트를 종합하여 LLM으로 최종 응답을 생성한다.

### Agent 내부 실행 흐름 (executor.py)

```
Agent.run(state)
  → AgentExecutor.execute(state)
    1) _run_retrieval  — 주입된 retriever가 있으면 순회하며 RAG 조회 (0개~N개)
    2) _run_tools      — 주입된 MCP tool이 있으면 순회하며 호출 (0개~N개)
    3) _run_llm        — 수집된 context + tool 결과로 LLM 호출
  → 갱신된 state 반환
```

현재는 등록된 tool을 순서대로 모두 호출하는 단순 파이프라인 방식이다.
추후 아래 중 하나로 교체하면 진짜 "에이전트" 동작이 가능하다:
- **LLM tool calling 루프**: LLM이 tool 선택 + args 생성 → 결과를 다시 LLM에 전달
- **ReAct 패턴**: Reasoning → Action → Observation 반복

---

## 프로젝트 구조

```
multi_agent_base/
├── workflow.py                  # GAIA 플랫폼 고정 진입점. StateGraph 조립 + compile
├── state.py                     # GraphState (추후 GaiaGraphState 상속으로 교체)
├── main.py                      # 로컬 개발/테스트용 진입점
├── .env.example                 # 환경변수 템플릿
├── pyproject.toml               # uv 기준 의존성 관리
│
├── config/
│   ├── settings.py              # pydantic-settings 기반 환경변수 로딩
│   └── intents.py               # Intent enum 정의
│
├── core/
│   ├── logging.py               # structlog 로거 + log_node_execution 데코레이터
│   ├── exceptions.py            # 커스텀 예외 계층
│   └── llm.py                   # ChatOpenAI 인스턴스 관리
│
├── nodes/
│   ├── intent_classifier.py     # intent 분류 노드
│   ├── router.py                # conditional routing 함수 (노드가 아닌 엣지 함수)
│   ├── unknown_handler.py       # UNKNOWN/오류 처리 노드
│   ├── final_response.py        # 최종 응답 생성 노드
│   └── agents/
│       ├── base_agent.py        # Agent 추상 클래스 (인터페이스)
│       ├── executor.py          # 공통 실행 로직 (RAG + Tool + LLM 조율)
│       ├── agent_a.py           # Domain Agent A
│       └── agent_b.py           # Domain Agent B
│
├── rag/
│   ├── base_retriever.py        # Retriever 추상 클래스 + Document 모델
│   ├── iflow_retriever.py       # iflow 블로그 Milvus retriever
│   └── xxx_retriever.py         # 추가 소스 retriever 예시
│
├── mcp/
│   ├── client.py                # MCP 클라이언트 (tool 등록/조회/호출)
│   └── tools/
│       ├── base_tool.py         # Tool 추상 클래스
│       ├── search_tool.py       # 검색 tool stub
│       └── summary_tool.py      # 요약 tool stub
│
└── prompts/
    ├── intent_classifier.py     # intent 분류 프롬프트
    └── agent_base.py            # agent 공통 프롬프트
```

---

## 개발자가 구현해야 하는 영역

현재 골격(scaffold)만 구현되어 있으며, 아래 영역에 실제 비즈니스 로직을 채워넣어야 한다.

### 반드시 구현

| 영역 | 파일 | 할 일 |
|------|------|-------|
| RAG 검색 로직 | `rag/iflow_retriever.py` | Milvus 벡터 검색 쿼리 구현 (`retrieve` 메서드) |
| RAG 검색 로직 | `rag/xxx_retriever.py` | 추가 소스 검색 로직 구현 |
| MCP Tool 로직 | `mcp/tools/search_tool.py` | 실제 검색 API 연동 (`call` 메서드) |
| MCP Tool 로직 | `mcp/tools/summary_tool.py` | 실제 요약 로직 연동 |
| MCP 서버 연결 | `mcp/client.py` | `connect()` 메서드에 실제 MCP 서버 연결 로직 |
| Agent 비즈니스 로직 | `nodes/agents/agent_a.py` | 도메인에 맞는 retriever/tool 조합 결정 |
| Agent 비즈니스 로직 | `nodes/agents/agent_b.py` | 도메인에 맞는 retriever/tool 조합 결정 |
| 프롬프트 튜닝 | `prompts/*.py` | 도메인에 맞게 프롬프트 조정 |

### 선택적 확장

| 영역 | 파일 | 할 일 |
|------|------|-------|
| Tool calling 고도화 | `nodes/agents/executor.py` | 단순 파이프라인 → LLM tool calling 루프 또는 ReAct 패턴으로 전환 |
| State 교체 | `state.py` | `TypedDict` → `GaiaGraphState` 상속으로 전환 |
| Intent 확장 | `config/intents.py` | 새 intent 추가 (아래 가이드 참조) |

---

## 설치 및 실행

```bash
# 의존성 설치 (uv 기준)
uv sync

# 환경변수 설정
cp .env.example .env
# .env 파일에서 OPENAI_API_KEY 등 값 입력

# 로컬 테스트 실행
uv run python main.py
```

---

## 확장 가이드

### 새 Intent + Agent 추가하기

예시: `INTENT_C` intent와 Agent C를 추가하는 경우.

**Step 1.** `config/intents.py` — `Intent` enum에 새 값 추가

```python
class Intent(str, Enum):
    INTENT_A = "INTENT_A"
    INTENT_B = "INTENT_B"
    INTENT_C = "INTENT_C"   # 추가
    UNKNOWN = "UNKNOWN"
```

**Step 2.** `nodes/agents/agent_c.py` — 새 Agent 파일 생성

```python
from nodes.agents.base_agent import BaseAgent
from nodes.agents.executor import AgentExecutor
from core.logging import log_node_execution
from state import GraphState

class AgentC(BaseAgent):
    def __init__(self) -> None:
        self._executor = AgentExecutor(
            retrievers=[...],       # 필요한 retriever 주입 (없으면 빈 리스트 또는 생략)
            mcp_client=...,         # 필요한 MCP client 주입 (없으면 생략)
            tools=["tool_name"],    # 사용할 tool 이름 (없으면 빈 리스트 또는 생략)
        )

    def run(self, state: GraphState) -> GraphState:
        return self._executor.execute(state)

_agent: AgentC | None = None

def _get_agent() -> AgentC:
    global _agent
    if _agent is None:
        _agent = AgentC()
    return _agent

@log_node_execution
def agent_c_node(state: GraphState) -> GraphState:
    return _get_agent().run(state)
```

**Step 3.** `nodes/router.py` — `INTENT_TO_NODE`에 매핑 추가

```python
INTENT_TO_NODE: dict[str, str] = {
    Intent.INTENT_A.value: "agent_a",
    Intent.INTENT_B.value: "agent_b",
    Intent.INTENT_C.value: "agent_c",     # 추가
    Intent.UNKNOWN.value: "unknown_handler",
}
```

**Step 4.** `workflow.py` — 노드 등록 및 엣지 연결

```python
from nodes.agents.agent_c import agent_c_node

# add_node
sg.add_node("agent_c", agent_c_node)

# add_conditional_edges 매핑에 추가
{
    "agent_a": "agent_a",
    "agent_b": "agent_b",
    "agent_c": "agent_c",               # 추가
    "unknown_handler": "unknown_handler",
}

# final_response로 연결
sg.add_edge("agent_c", "final_response")
```

### 새 RAG Retriever 추가하기

**Step 1.** `rag/` 폴더에 새 파일 생성 (예: `rag/confluence_retriever.py`)

```python
from rag.base_retriever import BaseRetriever, Document
from core.exceptions import RAGRetrievalError

class ConfluenceRetriever(BaseRetriever):
    def __init__(self, collection_name: str = "confluence") -> None:
        # Milvus 연결 설정 등
        ...

    def retrieve(self, query: str) -> list[Document]:
        # 실제 검색 로직 구현
        # 실패 시 RAGRetrievalError raise
        return [Document(page_content="...", metadata={...})]
```

**Step 2.** Agent 생성자에서 주입

```python
from rag.confluence_retriever import ConfluenceRetriever

self._executor = AgentExecutor(
    retrievers=[IflowRetriever(), ConfluenceRetriever()],  # 여러 개 조합 가능
    ...
)
```

### 새 MCP Tool 추가하기

**Step 1.** `mcp/tools/` 폴더에 새 파일 생성 (예: `mcp/tools/translate_tool.py`)

```python
from mcp.tools.base_tool import BaseTool

class TranslateTool(BaseTool):
    @property
    def name(self) -> str:
        return "translate"

    @property
    def description(self) -> str:
        return "텍스트를 번역한다."

    @property
    def args_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target_lang": {"type": "string"},
            },
            "required": ["text", "target_lang"],
        }

    def call(self, args: dict) -> dict:
        # 실제 번역 로직 구현
        # 실패 시 예외 raise (MCPClient가 MCPToolError로 래핑)
        return {"translated": "..."}
```

**Step 2.** Agent 생성자에서 MCPClient에 등록하고 tool 이름 지정

```python
from mcp.tools.translate_tool import TranslateTool

mcp_client = MCPClient()
mcp_client.register_tool(SearchTool())
mcp_client.register_tool(TranslateTool())  # 추가

self._executor = AgentExecutor(
    mcp_client=mcp_client,
    tools=["search", "translate"],  # 사용할 tool 이름 목록
    ...
)
```

---

## 횡단 관심사

- **로깅**: 모든 노드 함수에 `@log_node_execution` 데코레이터를 적용하면 진입/종료, 소요시간, intent, session_id가 자동으로 structlog에 기록된다.
- **예외 처리**: 모든 커스텀 예외는 `MultiAgentBaseError`를 상속하며, `cause`(원인 예외)와 `context`(추가 정보 dict)를 함께 전달할 수 있다.
- **LLM 관리**: `core/llm.py`의 `get_llm()`은 동일 설정으로 중복 생성되지 않도록 `lru_cache`로 관리된다.

## 기술 스택

- langgraph >= 1.0
- langchain >= 0.3, langchain-openai
- pymilvus (Milvus 벡터 DB)
- pydantic-settings (환경변수 관리)
- structlog (구조화된 로깅)
