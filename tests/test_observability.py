"""Testes de observabilidade: logs estruturados, trace_id e timings.

Valida:
- trace_id UUID gerado por execução
- node_timings registrados para cada nó executado
- Logger configurado e funcional
- Retry configurado em repo_tools
"""

import json
import logging
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.agent.graph import run_agent
from app.services.logger import (
    configure_logging,
    generate_trace_id,
    get_logger,
    measure_duration,
    log_node_start,
    log_node_end,
    log_audit_entry,
)


class TestTraceId:
    """Testes para geração e propagação de trace_id."""

    def test_generate_trace_id_is_uuid4(self):
        """trace_id gerado é UUID v4 válido."""
        trace_id = generate_trace_id()
        parsed = uuid.UUID(trace_id, version=4)
        assert str(parsed) == trace_id

    def test_run_agent_generates_trace_id(self):
        """run_agent gera trace_id único na execução."""
        result = run_agent("")
        assert "trace_id" in result
        assert result["trace_id"] != ""
        # Validar que é UUID
        uuid.UUID(result["trace_id"], version=4)

    def test_trace_id_unique_per_execution(self):
        """Cada execução gera trace_id diferente."""
        result1 = run_agent("")
        result2 = run_agent("")
        assert result1["trace_id"] != result2["trace_id"]


class TestNodeTimings:
    """Testes para registro de latência por nó."""

    def test_node_timings_present_in_result(self):
        """node_timings está presente no resultado."""
        result = run_agent("")
        assert "node_timings" in result
        assert isinstance(result["node_timings"], list)

    def test_node_timings_has_entries(self):
        """node_timings tem pelo menos 1 entrada (receive_input + validate_input)."""
        result = run_agent("")
        assert len(result["node_timings"]) >= 2

    def test_timing_entry_has_required_fields(self):
        """Cada timing entry tem node e duration_ms."""
        result = run_agent("")
        for entry in result["node_timings"]:
            assert "node" in entry
            assert "duration_ms" in entry
            assert isinstance(entry["duration_ms"], float)
            assert entry["duration_ms"] >= 0

    def test_full_flow_records_all_node_timings(self):
        """Fluxo completo registra timing de todos os nós executados."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                "# Projeto\n\nDescrição do projeto.\n\n"
                "## Instalação\n\npip install projeto\n"
            )
            result = run_agent(tmp)

            node_names = [t["node"] for t in result["node_timings"]]
            # Deve ter pelo menos os nós do fluxo completo
            assert "receive_input" in node_names
            assert "validate_input" in node_names
            assert "discover_docs" in node_names
            assert "merge_docs" in node_names
            assert "analyze_docs" in node_names
            assert "build_report" in node_names


class TestLogger:
    """Testes para o serviço de logging."""

    def test_configure_logging_does_not_raise(self):
        """configure_logging() executa sem erros."""
        configure_logging()

    def test_get_logger_returns_bound_logger(self):
        """get_logger retorna logger funcional."""
        log = get_logger("test")
        assert log is not None

    def test_measure_duration_returns_positive(self):
        """measure_duration retorna duration_ms >= 0."""
        with measure_duration() as timer:
            _ = sum(range(100))
        assert timer["duration_ms"] >= 0

    def test_log_node_start_does_not_raise(self):
        """log_node_start não lança exceção."""
        log = get_logger("test")
        log_node_start(log, "test_node", "trace-123")

    def test_log_node_end_does_not_raise(self):
        """log_node_end não lança exceção."""
        log = get_logger("test")
        log_node_end(log, "test_node", "trace-123", 42.5)

    def test_log_audit_entry_does_not_raise(self):
        """log_audit_entry não lança exceção."""
        log = get_logger("test")
        log_audit_entry(log, "trace-123", "test_event", key="value")


class TestRetry:
    """Testes para retry em repo_tools."""

    @patch("app.tools.repo_tools.requests.head")
    def test_retry_on_connection_error(self, mock_head):
        """Retry é tentado em caso de ConnectionError."""
        import requests as req
        from app.tools.repo_tools import validate_repository_url

        mock_head.side_effect = req.exceptions.ConnectionError("connection failed")

        valid, message = validate_repository_url("https://github.com/example/repo")

        assert valid is False
        assert "conexão" in message.lower() or "retry" in message.lower() or "connection" in message.lower()
        # Deve ter sido chamado 3 vezes (1 original + 2 retries)
        assert mock_head.call_count == 3

    @patch("app.tools.repo_tools.requests.head")
    def test_retry_succeeds_on_second_attempt(self, mock_head):
        """Retry funciona quando segunda tentativa sucede."""
        import requests as req
        from app.tools.repo_tools import validate_repository_url

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_head.side_effect = [
            req.exceptions.ConnectionError("first fail"),
            mock_response,
        ]

        valid, message = validate_repository_url("https://github.com/example/repo")

        assert valid is True
        assert mock_head.call_count == 2
