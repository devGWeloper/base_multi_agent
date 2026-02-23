# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest src/workflows/v1_0/test/

# Run a single test file
uv run pytest src/workflows/v1_0/test/unit/test_router.py

# Run a single test function
uv run pytest src/workflows/v1_0/test/unit/test_router.py::test_function_name

# Run local interactive mode
uv run python app.py
```

## Architecture

This is a LangGraph-based multi-agent system. The execution flow is:

```
User Input → Intent Classifier → Router → Agent A / Agent B / Unknown Handler → Final Response
```

**State** (`src/workflows/v1_0/state.py`): `GraphState` TypedDict with `messages` (accumulated via `operator.add`), `intent`, `agent_output`, `context`, `metadata`, `error`.

**Graph** (`src/workflows/v1_0/workflow.py`): Assembles and compiles the `StateGraph`. This is the GAIA platform entry point — `graph` is a module-level instance. `app.py` is for local interactive testing only.

**Nodes** (`src/workflows/v1_0/node/`):
- `intent_classifier.py` — LLM classifies intent; on failure sets `state["error"]` and continues (graceful degradation to unknown_handler)
- `router.py` — pure function mapping `state["intent"]` → node name via `INTENT_TO_NODE` dict
- `unknown_handler.py` — distinguishes system errors (`state["error"]`) from unmatched intents
- `final_response.py` — combines `agent_output` + `context`, generates final LLM response
- `base_agent.py` — this version's Agent interface (`BaseAgent` ABC). Kept in version folder, not `src/core/`, because the interface may change across versions
- `executor.py` — this version's execution pipeline: RAG retrieval → MCP tool calls → LLM inference (all sequential). Also version-scoped for the same reason
- `agents/` — **only domain Agent implementations** (agent_a.py, agent_b.py, …). Add new agents here.

**Agent pattern**: Each agent (`agent_a.py`, `agent_b.py`) uses lazy `_get_agent()` singleton to defer initialization. Retrievers and tools are injected into `AgentExecutor` at construction time.

**RAG** (`src/workflows/v1_0/rag/`): `BaseRetriever` → `retrieve(query) -> list[Document]`. Milvus-backed retrievers are currently stubs.

**MCP Tools** (`src/workflows/v1_0/mcp/`): `BaseTool` → `call(args: dict) -> dict`. `MCPClient` manages tool registration and dispatch. Tool implementations are currently stubs.

## Extending the System

**Add a new intent + agent:**
1. Add value to `src/workflows/v1_0/config/intents.py` `Intent` enum
2. Create `src/workflows/v1_0/node/domain/agent_c.py` — import `BaseAgent` from `nodes.base_agent`, `AgentExecutor` from `nodes.executor`
3. Add entry to `src/workflows/v1_0/node/router.py` `INTENT_TO_NODE` dict
4. Register node and edge in `src/workflows/v1_0/workflow.py`

**Add a new retriever:** Inherit `BaseRetriever` in `src/workflows/v1_0/rag/`, implement `retrieve()`, inject into `AgentExecutor(retrievers=[...])`.

**Add a new tool:** Inherit `BaseTool` in `src/workflows/v1_0/mcp/tool/`, implement `name`, `description`, `args_schema`, `call()`, register with `MCPClient`.

## Key Patterns

- **Error as state**: Classification failures set `state["error"]`; graph continues gracefully to unknown_handler
- **Logging**: `@log_node_execution` decorator (from `src/core/logging.py`) instruments node entry/exit, elapsed time, and exceptions with `intent` + `session_id`
- **LLM singleton**: `src/core/llm.py` `get_llm()` is `@lru_cache`; settings come from `config/settings.py` (also cached)
- **Config**: All environment variables loaded via `pydantic-settings` from `.env`. See `.env.example` for required keys (`OPENAI_API_KEY`, `OPENAI_MODEL_NAME`, `MILVUS_URI`, etc.)
- **Custom exceptions** (`src/core/exceptions.py`): All inherit `MultiAgentBaseError`; support `cause` (wrapped exception) and `context` (dict) fields
