"""Testes para endpoint webhook /api/analyze.

Valida:
- Endpoint responde corretamente
- Validação de entrada (URL obrigatória)
- Resposta estruturada com schema definido
- Health check funcional
- Integração com run_agent (mock)
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.webhook import api_app


@pytest.fixture
def client():
    """TestClient para o webhook API."""
    return TestClient(api_app)


class TestHealthCheck:
    """Testes para /api/health."""

    def test_health_returns_ok(self, client):
        """Health check retorna status ok."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAnalyzeEndpoint:
    """Testes para POST /api/analyze."""

    def test_empty_url_returns_400(self, client):
        """URL vazia retorna 400."""
        response = client.post("/api/analyze", json={"url": ""})
        assert response.status_code == 400

    def test_missing_url_returns_422(self, client):
        """Corpo sem campo url retorna 422."""
        response = client.post("/api/analyze", json={})
        assert response.status_code == 422

    def test_successful_analysis_returns_200(self, client):
        """Análise bem-sucedida retorna 200 com schema correto."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição do projeto.\n\n## Instalação\n\npip install x\n")

            response = client.post("/api/analyze", json={"url": tmp})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["trace_id"] != ""
            assert data["score"] is not None
            assert data["score"] >= 0
            assert data["score"] <= 10
            assert "dimensions" in data
            assert "report" in data
            assert data["report"] is not None

    def test_invalid_path_returns_error_status(self, client):
        """Caminho inexistente retorna status error."""
        response = client.post("/api/analyze", json={"url": "/caminho/inexistente"})

        assert response.status_code == 200
        data = response.json()
        # Validação inválida não gera exceção, gera status error
        assert data["status"] == "error"

    def test_response_has_required_fields(self, client):
        """Resposta contém todos os campos do schema."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Test\n\nContent here.\n")

            response = client.post("/api/analyze", json={"url": tmp})

            data = response.json()
            required_fields = ["status", "trace_id", "score", "dimensions",
                             "strengths_count", "issues_count", "report", "errors"]
            for field in required_fields:
                assert field in data, f"Campo '{field}' ausente na resposta"

    def test_accepts_input_type_parameter(self, client):
        """Parâmetro input_type é aceito."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Test\n\nContent.\n")

            response = client.post("/api/analyze", json={"url": tmp, "input_type": "path"})

            assert response.status_code == 200
