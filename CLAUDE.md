# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/unit/test_router.py

# Run a single test function
uv run pytest tests/unit/test_router.py::test_function_name

# Run local interactive mode
uv run python main.py
```

## Architecture

This is a LangGraph-based multi-agent system. The execution flow is:

```
User Input → Intent Classifier → Router → Agent A / Agent B / Unknown Handler → Final Response
```

**State** (`state.py`): `GraphState` TypedDict with `messages` (accumulated via `operator.add`), `intent`, `agent_output`, `context`, `metadata`, `error`.

**Graph** (`workflow.py`): Assembles and compiles the `StateGraph`. This is the GAIA platform entry point — `graph` is a module-level instance. `main.py` is for local interactive testing only.

**Nodes** (`nodes/`):
- `intent_classifier.py` — LLM classifies intent; on failure sets `state["error"]` and continues (graceful degradation to unknown_handler)
- `router.py` — pure function mapping `state["intent"]` → node name via `INTENT_TO_NODE` dict
- `unknown_handler.py` — distinguishes system errors (`state["error"]`) from unmatched intents
- `final_response.py` — combines `agent_output` + `context`, generates final LLM response
- `agents/executor.py` — core pipeline: RAG retrieval → MCP tool calls → LLM inference (all sequential)

**Agent pattern**: Each agent (`agent_a.py`, `agent_b.py`) uses lazy `_get_agent()` singleton to defer initialization. Retrievers and tools are injected into `AgentExecutor` at construction time.

**RAG** (`rag/`): `BaseRetriever` → `retrieve(query) -> list[Document]`. Milvus-backed retrievers are currently stubs.

**MCP Tools** (`mcp/`): `BaseTool` → `call(args: dict) -> dict`. `MCPClient` manages tool registration and dispatch. Tool implementations are currently stubs.

## Extending the System

**Add a new intent + agent:**
1. Add value to `config/intents.py` `Intent` enum
2. Create `nodes/agents/agent_c.py` inheriting `BaseAgent` / using `AgentExecutor`
3. Add entry to `nodes/router.py` `INTENT_TO_NODE` dict
4. Register node and edge in `workflow.py`

**Add a new retriever:** Inherit `BaseRetriever` in `rag/`, implement `retrieve()`, inject into `AgentExecutor(retrievers=[...])`.

**Add a new tool:** Inherit `BaseTool` in `mcp/tools/`, implement `name`, `description`, `args_schema`, `call()`, register with `MCPClient`.

## Key Patterns

- **Error as state**: Classification failures set `state["error"]`; graph continues gracefully to unknown_handler
- **Logging**: `@log_node_execution` decorator (from `core/logging.py`) instruments node entry/exit, elapsed time, and exceptions with `intent` + `session_id`
- **LLM singleton**: `core/llm.py` `get_llm()` is `@lru_cache`; settings come from `config/settings.py` (also cached)
- **Config**: All environment variables loaded via `pydantic-settings` from `.env`. See `.env.example` for required keys (`OPENAI_API_KEY`, `OPENAI_MODEL_NAME`, `MILVUS_URI`, etc.)
- **Custom exceptions** (`core/exceptions.py`): All inherit `MultiAgentBaseError`; support `cause` (wrapped exception) and `context` (dict) fields
