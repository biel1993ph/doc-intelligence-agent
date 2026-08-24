"""Serviço de observabilidade: logs estruturados JSON e trace."""

import logging
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

import structlog


def configure_logging() -> None:
    """Configura structlog com processador JSON e nível via LOG_LEVEL.

    Deve ser chamado uma vez na inicialização da aplicação.
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Obtém logger estruturado com o nome fornecido."""
    return structlog.get_logger(name)


def generate_trace_id() -> str:
    """Gera trace_id UUID v4 único para correlação de uma execução."""
    return str(uuid.uuid4())


@contextmanager
def measure_duration():
    """Context manager que mede duração em milissegundos.

    Uso:
        with measure_duration() as timer:
            # operação
        duration_ms = timer["duration_ms"]
    """
    result = {"duration_ms": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        elapsed = time.perf_counter() - start
        result["duration_ms"] = round(elapsed * 1000, 2)


def log_node_start(logger: structlog.stdlib.BoundLogger, node: str, trace_id: str) -> None:
    """Loga entrada em um nó do grafo."""
    logger.info(
        "node_start",
        node=node,
        trace_id=trace_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def log_node_end(
    logger: structlog.stdlib.BoundLogger,
    node: str,
    trace_id: str,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Loga saída de um nó do grafo."""
    log_data = {
        "node": node,
        "trace_id": trace_id,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
    }
    if error:
        log_data["error"] = error

    if success:
        logger.info("node_end", **log_data)
    else:
        logger.error("node_end", **log_data)


def log_audit_entry(
    logger: structlog.stdlib.BoundLogger,
    trace_id: str,
    event: str,
    **kwargs,
) -> None:
    """Registra entrada de auditoria para trace/reconstrução de execução."""
    logger.info(
        event,
        trace_id=trace_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **kwargs,
    )


# Configurar na importação
configure_logging()
