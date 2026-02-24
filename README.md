# Multi-Agent Base Project

LangGraph + LangChain 기반 Multi-Agent 아키텍처 **골격(scaffold) 프로젝트**.
GAIA 플랫폼 위에서 동작하며, 이 프로젝트를 복사하여 도메인별 비즈니스 로직만 채워넣는 방식으로 여러 프로젝트를 찍어낼 수 있다.

---

## 목차

1. [전체 아키텍처](#전체-아키텍처)
2. [프로젝트 구조 — 설계 의도](#프로젝트-구조--설계-의도)
3. [파일별 역할 상세](#파일별-역할-상세)
4. [개발자 작업 가이드 — 건드려야 할 파일 vs 건드리면 안 되는 파일](#개발자-작업-가이드--건드려야-할-파일-vs-건드리면-안-되는-파일)
5. [Python 경로 설정 원리](#python-경로-설정-원리)
6. [설치 및 실행](#설치-및-실행)
7. [테스트](#테스트)
8. [확장 가이드](#확장-가이드)
9. [횡단 관심사](#횡단-관심사)
10. [기술 스택](#기술-스택)

---

## 전체 아키텍처

### 실행 흐름

```
User Input
  → Intent Classifier  (LLM으로 intent 분류)
  → Router             (intent 값 → 다음 노드 결정, conditional edge)
  ┌─→ Agent A ──┐
  ├─→ Agent B ──┤→ Final Response → END
  └─→ Default  ─┘   (agent_output + context → 최종 응답 생성)
```

| 노드 | 역할 |
|------|------|
| **Intent Classifier** | 사용자 입력을 LLM으로 분석해 `Intent` enum 값으로 분류. 실패 시 예외를 던지지 않고 `state["error"]`에 기록 후 `UNKNOWN`으로 fallback (graceful degradation) |
| **Router** | `state["intent"]`를 보고 다음 노드 이름을 반환하는 **순수 함수**. 별도 노드가 아닌 conditional edge 함수 |
| **Domain Agent** | intent별 처리 담당. 생성 시 RAG retriever와 MCP tool을 **선택적으로 주입**받아 `AgentExecutor`에 위임 |
| **Default Response** | `UNKNOWN` intent 또는 분류 오류 처리. `state["error"]` 유무로 시스템 오류와 단순 미매칭을 구분 |
| **Final Response** | `agent_output` + RAG context를 종합해 LLM으로 최종 응답 생성 |

### Agent 내부 실행 흐름 (`_executor.py`)

```
Agent.run(state)
  └─→ AgentExecutor.execute(state)
        1) _run_retrieval  — 주입된 retriever 순회, RAG 조회 (0개~N개)
        2) _run_tools      — 주입된 MCP tool 순회, 호출 (0개~N개)
        3) _run_llm        — 수집된 context + tool 결과로 LLM 호출
        └─→ 갱신된 state 반환
```

현재는 등록된 tool을 순서대로 모두 호출하는 **단순 파이프라인** 방식.
추후 아래 중 하나로 교체하면 진짜 "에이전트" 동작이 가능하다:

- **LLM tool calling 루프**: LLM이 tool 선택 + args 생성 → 결과를 다시 LLM에 전달
- **ReAct 패턴**: Reasoning → Action → Observation 반복

---

## 프로젝트 구조 — 설계 의도

```
multi_agent_base/
├── app.py                          # 로컬 테스트 전용 진입점
├── pyproject.toml
├── .env.example
│
└── src/
    └── workflows/                  # [플랫폼 단위] 버전별로 격리
        ├── v1_0/                   # 운영 버전
        │   ├── workflow.py         ← GAIA 플랫폼 진입점 (graph 인스턴스)
        │   ├── state.py
        │   ├── core/               ← [이 버전의 공유 인프라] logging, exceptions, llm
        │   ├── config/
        │   ├── node/
        │   │   ├── _base_agent.py     ← 이 버전의 Agent 인터페이스 (수정 금지)
        │   │   ├── _executor.py       ← 이 버전의 실행 엔진 (수정 금지)
        │   │   └── domain/            ← Agent 구현체만 추가하는 곳
        │   ├── prompt/
        │   ├── rag/
        │   ├── mcp/
        │   └── test/
        └── v1_1/                   # 다음 버전 (v1_0 복사 후 독립 수정)
            └── (v1_0과 동일 구조)
```

### 왜 이 구조인가?

#### 1. `src/workflows/v1_x/` — 버전별 완전 격리

GAIA 플랫폼은 **특정 버전 폴더 안의 `workflow.py`만 읽어서 실행**한다.
버전 폴더는 서로 완전히 독립적이므로, `v1_1`을 개발·배포해도 `v1_0` 운영에 영향을 주지 않는다.
새 버전이 필요할 때는 `cp -r v1_0 v1_1` 후 해당 폴더 안에서만 작업한다.

```
# 버전 간 의존 금지 — 아래는 절대 해서는 안 됨
# from workflows.v1_0.xxx import ...  (v1_1 코드 안에서)
```

#### 2. `core/` — 버전 폴더 안의 인프라 레이어

`llm.py`, `logging.py`, `exceptions.py`는 LLM 클라이언트 관리, 구조화 로깅, 예외 계층처럼 **해당 버전 안에서 도메인과 무관하게 공유되는 인프라 코드**다.
각 버전 폴더(`v1_0/core/`, `v1_1/core/`) 안에 두어, 버전이 달라져도 서로 독립적으로 수정·진화할 수 있다.

#### 3. `base_agent.py`, `base_retriever.py`, `base_tool.py`, `executor.py` — 버전 폴더 안에 위치

이 파일들은 **해당 버전의 Agent/RAG/Tool 인터페이스 정의**다.
`v1_1`에서 `BaseAgent`의 인터페이스가 바뀌거나 `executor.py`가 ReAct 패턴으로 교체되어도 `v1_0`은 영향받지 않는다.

#### 4. `prompt/` — 노드 코드와 분리

프롬프트는 LLM 튜닝 과정에서 가장 자주 바뀌는 영역이다.
노드 로직(`node/`)과 분리해 두면, 프롬프트만 수정할 때 실행 코드를 건드릴 필요가 없다.

#### 레이어 간 의존 방향

```
app.py
  └─→ src/workflows/v1_0/workflow.py
        ├─→ node/        ──→  prompt/
        │                ──→  rag/
        │                ──→  mcp/
        │                ──→  config/
        │                └─→  state.py
        └─→ core/             (버전 내 공유 인프라)
```

의존 방향은 항상 **단방향 하향**. `core/`가 특정 노드 코드를 참조하거나, 버전 간 코드가 서로 참조하는 것은 금지.

---

## 파일별 역할 상세

### `core/` — 버전별 공유 인프라

| 파일 | 클래스/함수 | 역할 |
|------|------------|------|
| `exceptions.py` | `MultiAgentBaseError` | 프로젝트 공통 베이스 예외. `cause`(원인 예외)와 `context`(추가 정보 dict)를 함께 전달 가능 |
| | `IntentClassificationError` | Intent 분류 실패 |
| | `AgentExecutionError` | Agent 실행 중 오류 |
| | `RAGRetrievalError` | RAG 검색 실패 |
| | `MCPConnectionError` | MCP 서버 연결 실패 |
| | `MCPToolError` | MCP Tool 호출 실패 |
| `llm.py` | `get_llm()` | `@lru_cache` 싱글턴. 동일 설정으로 `ChatOpenAI` 인스턴스가 중복 생성되지 않도록 관리 |
| | `call_llm(messages, tools)` | LLM 호출 wrapper. `tools`가 있으면 `bind_tools` 후 호출 |
| `logging.py` | `get_logger(name)` | `structlog` 기반 구조화 로거 반환 |
| | `@log_node_execution` | 노드 함수 데코레이터. 진입/종료, 소요시간, `intent`, `session_id` 자동 로깅. 예외 발생 시 `node_error` 로그 후 re-raise |

---

### `src/workflows/v1_0/` — 워크플로우 핵심

#### `workflow.py` — GAIA 플랫폼 진입점

```python
graph = build_graph()   # 모듈 로드 시 자동 생성되는 컴파일된 그래프 인스턴스
```

GAIA 플랫폼은 이 `graph` 객체를 직접 임포트해서 실행한다.
새 노드를 추가할 때만 수정한다.

#### `state.py` — 그래프 공유 상태

```python
class GraphState(TypedDict):
    messages:     Annotated[list[BaseMessage], operator.add]  # 메시지 누적
    intent:       str        # 분류된 intent 값
    agent_output: str        # Agent가 생성한 텍스트
    context:      list[str]  # RAG 조회 결과 누적
    metadata:     dict       # session_id 등 부가 정보
    error:        str | None # 시스템 오류 메시지 (없으면 None)
```

모든 노드는 이 `GraphState`를 받아서 갱신된 dict를 반환한다.

#### `config/`

| 파일 | 역할 |
|------|------|
| `intents.py` | `Intent` enum 정의. 여기에 값을 추가해야 새 intent가 시스템에 인식됨 |
| `settings.py` | `pydantic-settings` 기반 환경변수 로딩. `@lru_cache` 싱글턴. `.env`에서 값을 읽음 |

#### `node/` — LangGraph 노드 함수

| 파일 | 함수 | 역할 |
|------|------|------|
| `intent_classifier.py` | `classify_intent(state)` | 사용자 입력을 LLM으로 분석해 `Intent` 값 결정. 실패 시 `state["error"]` 기록 후 `UNKNOWN` 설정 |
| `router.py` | `route_by_intent(state)` | `state["intent"]` → 다음 노드 이름 반환. `INTENT_TO_NODE` dict로 매핑. 노드가 아닌 conditional edge 함수 |
| `default_response.py` | `default_response(state)` | `UNKNOWN` intent 처리. `state["error"]` 있으면 시스템 오류 메시지, 없으면 미매칭 안내 메시지 |
| `final_response.py` | `generate_final_response(state)` | `agent_output` + `context`를 종합해 LLM으로 사용자에게 전달할 최종 응답 생성 |

#### `node/_base_agent.py`, `node/_executor.py` — 이 버전의 Agent 기반 코드

| 파일 | 클래스/함수 | 역할 |
|------|------------|------|
| `_base_agent.py` | `BaseAgent(ABC)` | **이 버전의** Agent 인터페이스 정의. `run(state) → state` 추상 메서드만 선언. 버전 간 인터페이스가 달라질 수 있으므로 버전 폴더에 위치 |
| `_executor.py` | `AgentExecutor` | **이 버전의** 공통 실행 엔진. 생성 시 retriever 목록, MCP client, tool 이름 목록을 주입받아 `execute(state)`에서 RAG → Tool → LLM 순서로 실행 |

#### `node/domain/` — 도메인 Agent 구현체만

이 폴더의 역할은 단 하나: **도메인별 Agent 파일을 추가하는 곳**.
`_base_agent.py`와 `_executor.py`는 한 레벨 위(`node/`)에 있으므로, 이 폴더에는 비즈니스 로직 Agent만 존재한다.

| 파일 | 클래스/함수 | 역할 |
|------|------------|------|
| `domain_node_a.py` | `AgentA` / `agent_a_node` | Domain Agent A 구현체. `_get_agent()` lazy singleton 패턴으로 최초 호출 시 1회만 초기화. `agent_a_node`가 실제 LangGraph 노드 함수 |
| `domain_node_b.py` | `AgentB` / `agent_b_node` | Domain Agent B (구조 동일) |

#### `prompt/` — LLM 프롬프트 상수

| 파일 | 내용 |
|------|------|
| `intent_classifier_prompt.py` | Intent 분류용 system/user 프롬프트 템플릿 |
| `default_response_prompt.py` | Default Response 노드용 프롬프트 |
| `final_response_prompt.py` | 최종 응답 생성용 프롬프트 |
| `domain/domain_node_a_prompt.py` | Domain Node A 전용 system/user 프롬프트 (`{context}`, `{user_input}` 변수 포함) |
| `domain/domain_node_b_prompt.py` | Domain Node B 전용 프롬프트 |

#### `rag/` — RAG 검색 레이어

| 파일 | 클래스 | 역할 |
|------|--------|------|
| `base_retriever.py` | `BaseRetriever(ABC)` | `retrieve(query) → list[Document]` 추상 메서드 정의 |
| | `Document` | `page_content: str`, `metadata: dict` 데이터 모델 |
| `iflow_retriever.py` | `IflowRetriever` | Milvus 벡터 DB 기반 iflow 블로그 검색 (현재 stub) |
| `xxx_retriever.py` | `XxxRetriever` | 추가 소스 검색 예시 (현재 stub) |

#### `mcp/` — MCP Tool 레이어

| 파일 | 클래스 | 역할 |
|------|--------|------|
| `client.py` | `MCPClient` | Tool 등록(`register_tool`), 조회(`get_tool`), 호출(`call_tool`) 관리. 호출 실패는 `MCPToolError`로 래핑 |
| `tool/base_tool.py` | `BaseTool(ABC)` | Tool 인터페이스 정의. `name`, `description`, `args_schema` property + `call(args) → dict` 추상 메서드 |
| `tool/search_tool.py` | `SearchTool` | 검색 tool 구현체 (현재 stub) |
| `tool/summary_tool.py` | `SummaryTool` | 요약 tool 구현체 (현재 stub) |

#### `test/`

| 경로 | 내용 |
|------|------|
| `conftest.py` | pytest fixture. `GraphState` 기본값, mock LLM 등 공통 fixture 정의 |
| `unit/` | 노드 함수 단위 테스트 (LLM/외부 의존성 mock 처리) |
| `integration/` | 그래프 전체 흐름 통합 테스트 |

---

## 개발자 작업 가이드 — 건드려야 할 파일 vs 건드리면 안 되는 파일

### 수정 금지 — 프레임워크 코드

아래 파일들은 **골격 프로젝트가 제공하는 실행 엔진**이다.
비즈니스 로직을 구현하는 과정에서 이 파일들을 수정할 필요는 없다.
수정이 필요하다고 느껴진다면, 확장 포인트(`base_*` 상속, 주입)를 먼저 검토할 것.

| 파일 | 이유 |
|------|------|
| `src/workflows/v1_0/core/exceptions.py` | 예외 계층은 고정. 새 예외가 필요하면 기존 클래스를 상속 |
| `src/workflows/v1_0/core/llm.py` | LLM 클라이언트 관리 로직. 모델 변경은 `.env`로 |
| `src/workflows/v1_0/core/logging.py` | 로깅 인프라. 모든 노드에서 동일하게 사용 |
| `src/workflows/v1_0/node/_base_agent.py` | Agent 인터페이스 정의. 변경 시 모든 Agent에 영향 |
| `src/workflows/v1_0/node/_executor.py` | 공통 실행 엔진. ReAct 등으로 교체할 때만 수정 (선택적 고도화) |
| `src/workflows/v1_0/rag/base_retriever.py` | Retriever 인터페이스. 변경 시 모든 Retriever에 영향 |
| `src/workflows/v1_0/mcp/tool/base_tool.py` | Tool 인터페이스. 변경 시 모든 Tool에 영향 |
| `src/workflows/v1_0/mcp/client.py` | Tool 등록/호출 관리. 기능 추가가 아닌 한 수정 불필요 |
| `app.py` | 로컬 테스트 진입점. 구조 변경 불필요 |

---

### 반드시 구현 — 비즈니스 로직

이 파일들은 **골격만 제공된 stub**이다. 실제 도메인에 맞게 구현해야 한다.

#### 1단계: Intent 정의

| 파일 | 할 일 |
|------|-------|
| `src/workflows/v1_0/config/intents.py` | 도메인에 맞는 `Intent` enum 값 추가/수정 |

#### 2단계: 프롬프트 작성

| 파일 | 할 일 |
|------|-------|
| `src/workflows/v1_0/prompt/intent_classifier_prompt.py` | 도메인 컨텍스트를 반영한 분류 프롬프트 작성 |
| `src/workflows/v1_0/prompt/domain/domain_node_a_prompt.py` | Domain Node A의 역할과 출력 형식 정의 |
| `src/workflows/v1_0/prompt/domain/domain_node_b_prompt.py` | Domain Node B의 역할과 출력 형식 정의 |
| `src/workflows/v1_0/prompt/final_response_prompt.py` | 최종 응답 톤·형식 정의 |

#### 3단계: RAG 구현

| 파일 | 할 일 |
|------|-------|
| `src/workflows/v1_0/rag/iflow_retriever.py` | `retrieve(query)` 메서드에 Milvus 벡터 검색 로직 구현 |
| `src/workflows/v1_0/rag/xxx_retriever.py` | 추가 검색 소스 구현 (필요 시) |

#### 4단계: MCP Tool 구현

| 파일 | 할 일 |
|------|-------|
| `src/workflows/v1_0/mcp/tool/search_tool.py` | `call(args)` 메서드에 실제 검색 API 연동 |
| `src/workflows/v1_0/mcp/tool/summary_tool.py` | `call(args)` 메서드에 실제 요약 로직 연동 |

#### 5단계: Agent 조합 결정

| 파일 | 할 일 |
|------|-------|
| `src/workflows/v1_0/node/domain/domain_node_a.py` | `AgentExecutor`에 Agent A가 사용할 retriever/tool 조합 주입 |
| `src/workflows/v1_0/node/domain/domain_node_b.py` | `AgentExecutor`에 Agent B가 사용할 retriever/tool 조합 주입 |

---

### 조건부 수정 — 구조 변경 시만

| 파일 | 수정 시점 |
|------|----------|
| `src/workflows/v1_0/workflow.py` | 새 Agent 노드를 추가하거나 그래프 구조를 변경할 때 |
| `src/workflows/v1_0/state.py` | `GraphState`에 새 필드가 필요할 때 |
| `src/workflows/v1_0/node/router.py` | 새 intent 추가로 라우팅 매핑이 늘어날 때 |

---

## Python 경로 설정 원리

이 프로젝트는 flat import 방식을 사용한다.

```python
# 패키지 전체 경로가 아닌 flat import
from core.exceptions import AgentExecutionError    # src/workflows/v1_0/core/exceptions.py
from node._executor import AgentExecutor           # src/workflows/v1_0/node/_executor.py
from config.intents import Intent                  # src/workflows/v1_0/config/intents.py
```

`core/`를 포함한 모든 패키지가 버전 폴더 안에 있으므로, Python path에 등록할 경로는 하나뿐이다.

| 경로 | 역할 |
|------|------|
| `src/workflows/v1_0/` | `from core.xxx`, `from node.xxx`, `from config.xxx` 등 모든 import가 이 경로를 기준으로 해석됨 |

| 실행 방식 | 경로 등록 방법 |
|----------|--------------|
| `pytest` | `pyproject.toml`의 `pythonpath = ["src/workflows/v1_0"]` |
| `app.py` | 파일 상단 `sys.path.insert`로 자동 등록 |

---


## 테스트

```bash
# 전체 테스트
uv run pytest src/workflows/v1_0/test/

# 단위 테스트만
uv run pytest src/workflows/v1_0/test/unit/

# 통합 테스트만
uv run pytest src/workflows/v1_0/test/integration/

# 특정 파일
uv run pytest src/workflows/v1_0/test/unit/test_router.py

# 특정 함수
uv run pytest src/workflows/v1_0/test/unit/test_router.py::test_function_name
```

---

## 확장 가이드

### 새 Intent + Agent 추가

예시: `INTENT_C`와 Agent C 추가.

**Step 1.** `config/intents.py`

```python
class Intent(str, Enum):
    INTENT_A = "INTENT_A"
    INTENT_B = "INTENT_B"
    INTENT_C = "INTENT_C"   # 추가
    UNKNOWN  = "UNKNOWN"
```

**Step 2.** `node/domain/domain_node_c.py` 생성

```python
from node._base_agent import BaseAgent
from node._executor import AgentExecutor
from core.logging import log_node_execution
from state import GraphState

class AgentC(BaseAgent):
    def __init__(self) -> None:
        self._executor = AgentExecutor(
            system_prompt=AGENT_C_SYSTEM_PROMPT,
            user_prompt_template=AGENT_C_USER_PROMPT,
            retrievers=[IflowRetriever()],   # 필요 없으면 생략
            mcp_client=mcp_client,           # 필요 없으면 생략
            tools=["search"],
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

**Step 3.** `node/router.py` — 매핑 추가

```python
INTENT_TO_NODE: dict[str, str] = {
    Intent.INTENT_A.value: "agent_a",
    Intent.INTENT_B.value: "agent_b",
    Intent.INTENT_C.value: "agent_c",   # 추가
    Intent.UNKNOWN.value:  "default_response",
}
```

**Step 4.** `workflow.py` — 노드/엣지 등록

```python
from node.domain.domain_node_c import agent_c_node

sg.add_node("agent_c", agent_c_node)
# conditional_edges 매핑에 "agent_c": "agent_c" 추가
sg.add_edge("agent_c", "final_response")
```

---

### 새 RAG Retriever 추가

```python
# src/workflows/v1_0/rag/confluence_retriever.py
from rag.base_retriever import BaseRetriever, Document
from core.exceptions import RAGRetrievalError

class ConfluenceRetriever(BaseRetriever):
    def retrieve(self, query: str) -> list[Document]:
        # 실패 시 RAGRetrievalError raise
        return [Document(page_content="...", metadata={})]
```

Agent 생성자에서 주입:

```python
AgentExecutor(
    retrievers=[IflowRetriever(), ConfluenceRetriever()],  # 여러 개 조합 가능
    ...
)
```

---

### 새 MCP Tool 추가

```python
# src/workflows/v1_0/mcp/tool/translate_tool.py
from mcp.tool.base_tool import BaseTool

class TranslateTool(BaseTool):
    @property
    def name(self) -> str: return "translate"

    @property
    def description(self) -> str: return "텍스트를 번역한다."

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
        return {"translated": "..."}
```

Agent 생성자에서 등록:

```python
mcp_client = MCPClient()
mcp_client.register_tool(TranslateTool())

AgentExecutor(mcp_client=mcp_client, tools=["translate"], ...)
```

---

### 새 워크플로우 버전 추가

```bash
cp -r src/workflows/v1_0 src/workflows/v2_0
```

`pyproject.toml`의 `testpaths`와 `pythonpath`를 새 버전으로 교체하거나, 버전별 별도 pytest 설정을 관리한다.
`core/`를 포함한 모든 코드가 버전 폴더 안에 있으므로, 복사 후 두 버전은 완전히 독립적으로 수정·운영할 수 있다.

---

## 횡단 관심사

| 관심사 | 위치 | 내용 |
|--------|------|------|
| **로깅** | `core/logging.py` | `@log_node_execution` 데코레이터를 노드 함수에 적용하면 진입/종료, 소요시간, `intent`, `session_id`가 structlog에 자동 기록 |
| **예외** | `core/exceptions.py` | 모든 커스텀 예외는 `MultiAgentBaseError` 상속. `cause`와 `context` 필드로 디버깅 정보 전달 |
| **LLM 관리** | `core/llm.py` | `get_llm()`은 `@lru_cache` 싱글턴으로 중복 생성 방지. 모델 설정은 `.env`에서 |
| **설정** | `config/settings.py` | `get_settings()`도 `@lru_cache` 싱글턴. `.env` 또는 환경변수에서 읽음 |
| **Error as State** | `intent_classifier.py` | 분류 실패 등 내부 오류는 예외로 전파하지 않고 `state["error"]`에 기록. 그래프가 `default_response`로 graceful degradation |
