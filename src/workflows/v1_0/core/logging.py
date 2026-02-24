# structlog 기반 구조화된 로거 설정 및 log_node_execution 데코레이터
from __future__ import annotations

import functools
import time
from typing import Any, Callable

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def log_node_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """노드 함수에 적용하여 진입/종료, 소요시간, intent, session_id를 자동 로깅한다."""
    logger = get_logger(func.__qualname__)

    @functools.wraps(func)
    def wrapper(state: dict[str, Any]) -> dict[str, Any]:
        intent = state.get("intent", "N/A")
        session_id = state.get("metadata", {}).get("session_id", "N/A")
        logger.info(
            "node_enter",
            node=func.__name__,
            intent=intent,
            session_id=session_id,
        )
        start = time.perf_counter()
        try:
            result = func(state)
            elapsed = round(time.perf_counter() - start, 4)
            logger.info(
                "node_exit",
                node=func.__name__,
                intent=intent,
                session_id=session_id,
                elapsed_seconds=elapsed,
            )
            return result
        except Exception:
            elapsed = round(time.perf_counter() - start, 4)
            logger.exception(
                "node_error",
                node=func.__name__,
                intent=intent,
                session_id=session_id,
                elapsed_seconds=elapsed,
            )
            raise

    return wrapper
