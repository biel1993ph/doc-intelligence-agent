"""Testes para memória persistente: histórico de análises em SQLite.

Valida:
- Persistência de análise no banco
- Recuperação de histórico por source_key
- Geração de source_key consistente
- Seção "Histórico" no relatório quando há análises anteriores
- Integração end-to-end com run_agent
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.analysis_history import (
    generate_source_key,
    save_analysis,
    get_history,
)
from app.services.report_service import generate_report_markdown


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Usa banco SQLite temporário para cada teste."""
    with patch.dict(os.environ, {"ANALYSIS_DB_DIR": str(tmp_path)}):
        yield tmp_path


class TestSourceKey:
    """Testes para geração de chave de agrupamento."""

    def test_same_input_same_key(self):
        """Mesma entrada gera mesma chave."""
        key1 = generate_source_key("https://github.com/owner/repo")
        key2 = generate_source_key("https://github.com/owner/repo")
        assert key1 == key2

    def test_trailing_slash_normalized(self):
        """Trailing slash é normalizado."""
        key1 = generate_source_key("https://github.com/owner/repo")
        key2 = generate_source_key("https://github.com/owner/repo/")
        assert key1 == key2

    def test_case_insensitive(self):
        """URL é normalizada para lowercase."""
        key1 = generate_source_key("https://github.com/Owner/Repo")
        key2 = generate_source_key("https://github.com/owner/repo")
        assert key1 == key2

    def test_different_input_different_key(self):
        """Entradas diferentes geram chaves diferentes."""
        key1 = generate_source_key("https://github.com/owner/repo1")
        key2 = generate_source_key("https://github.com/owner/repo2")
        assert key1 != key2


class TestPersistence:
    """Testes para salvar e recuperar histórico."""

    def test_save_and_retrieve(self):
        """Análise salva é recuperável."""
        raw_input = "https://github.com/test/repo"
        analysis = {
            "score": 7,
            "dimensions": {"clareza": "adequada", "cobertura": "parcial"},
            "issues": [{"observation": "Falta X", "recommendation": "Add X"}],
            "strengths": ["Boa estrutura", "Exemplos presentes"],
        }

        save_analysis(raw_input, analysis)
        history = get_history(raw_input)

        assert len(history) == 1
        assert history[0]["score"] == 7
        assert history[0]["dimensions"]["clareza"] == "adequada"
        assert history[0]["findings_count"] == 1
        assert history[0]["strengths_count"] == 2

    def test_multiple_analyses_ordered(self):
        """Múltiplas análises são retornadas em ordem decrescente."""
        raw_input = "https://github.com/test/repo"

        save_analysis(raw_input, {"score": 5, "dimensions": {}, "issues": [], "strengths": []})
        save_analysis(raw_input, {"score": 7, "dimensions": {}, "issues": [], "strengths": []})
        save_analysis(raw_input, {"score": 8, "dimensions": {}, "issues": [], "strengths": []})

        history = get_history(raw_input)

        assert len(history) == 3
        # Mais recente primeiro
        assert history[0]["score"] == 8
        assert history[1]["score"] == 7
        assert history[2]["score"] == 5

    def test_different_repos_isolated(self):
        """Históricos de repositórios diferentes não se misturam."""
        save_analysis("https://github.com/a/repo1", {"score": 5, "dimensions": {}, "issues": [], "strengths": []})
        save_analysis("https://github.com/b/repo2", {"score": 9, "dimensions": {}, "issues": [], "strengths": []})

        history1 = get_history("https://github.com/a/repo1")
        history2 = get_history("https://github.com/b/repo2")

        assert len(history1) == 1
        assert history1[0]["score"] == 5
        assert len(history2) == 1
        assert history2[0]["score"] == 9

    def test_empty_history_for_new_repo(self):
        """Repositório nunca analisado retorna lista vazia."""
        history = get_history("https://github.com/new/repo")
        assert history == []

    def test_limit_parameter(self):
        """Parâmetro limit restringe número de resultados."""
        raw_input = "https://github.com/test/repo"
        for i in range(10):
            save_analysis(raw_input, {"score": i, "dimensions": {}, "issues": [], "strengths": []})

        history = get_history(raw_input, limit=3)
        assert len(history) == 3


class TestReportWithHistory:
    """Testes para seção Histórico no relatório."""

    def test_report_includes_history_section(self):
        """Relatório inclui seção Histórico quando há análises anteriores."""
        analysis = {
            "dimensions": {"clareza": "adequada"},
            "strengths": ["Boa estrutura"],
            "issues": [],
            "score": 8,
            "justification": "Documentação boa. Análise completa.",
            "base_insuficiente": False,
        }
        history = [
            {"score": 6, "analyzed_at": "2024-05-01T12:00:00Z", "findings_count": 3, "strengths_count": 2},
        ]

        report = generate_report_markdown(analysis, ["README.md"], None, history)

        assert "Histórico" in report
        assert "Evolução" in report
        assert "nota anterior 6" in report
        assert "nota atual 8" in report

    def test_report_no_history_section_when_empty(self):
        """Relatório não inclui seção Histórico quando não há análises anteriores."""
        analysis = {
            "dimensions": {"clareza": "adequada"},
            "strengths": ["Boa estrutura"],
            "issues": [],
            "score": 7,
            "justification": "Documentação razoável. Análise completa.",
            "base_insuficiente": False,
        }

        report = generate_report_markdown(analysis, ["README.md"], None, [])
        assert "Histórico" not in report

        report2 = generate_report_markdown(analysis, ["README.md"], None, None)
        assert "Histórico" not in report2


class TestEndToEnd:
    """Testes end-to-end de memória integrada ao agente."""

    def test_run_agent_persists_analysis(self):
        """run_agent salva análise no histórico."""
        from app.agent.graph import run_agent

        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição do projeto.\n\n## Instalação\n\npip install x\n")

            run_agent(tmp)

            history = get_history(tmp)
            assert len(history) == 1
            assert history[0]["score"] >= 0

    def test_second_run_has_history(self):
        """Segunda execução do mesmo repo recupera histórico."""
        from app.agent.graph import run_agent

        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição do projeto.\n\n## Uso\n\nExemplo.\n")

            # Primeira execução
            run_agent(tmp)

            # Segunda execução — deve ter histórico
            result = run_agent(tmp)

            # O relatório deve conter seção Histórico
            assert result["final_report"] is not None
            assert "Histórico" in result["final_report"]
            assert "Evolução" in result["final_report"]
