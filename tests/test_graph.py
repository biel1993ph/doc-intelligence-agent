"""Testes para o grafo LangGraph: compilação, roteamento e isolamento."""

import tempfile
from pathlib import Path

from app.agent.graph import build_graph, run_agent


def test_graph_compiles() -> None:
    """Grafo compila sem erros."""
    graph = build_graph()
    assert graph is not None


def test_run_agent_empty_input_stops_at_validation() -> None:
    """Entrada vazia: para em validate_input com status invalid."""
    result = run_agent("")

    assert result["validation_status"] == "invalid"
    assert result["input_type"] == "empty"
    # Não deve ter avançado para discover_docs
    assert result["discovered_files"] == []
    assert result["merged_context"] is None
    assert result["final_report"] is None


def test_run_agent_invalid_url_stops_at_validation() -> None:
    """URL inválida: para em validate_input."""
    result = run_agent("ftp://invalid-scheme.com/repo")

    assert result["validation_status"] == "invalid"
    assert result["discovered_files"] == []
    assert result["final_report"] is None


def test_run_agent_nonexistent_path_stops_at_validation() -> None:
    """Caminho inexistente: para em validate_input."""
    result = run_agent("/caminho/que/nao/existe/nada")

    assert result["validation_status"] == "invalid"
    assert result["final_report"] is None


def test_run_agent_empty_dir_stops_at_discovery() -> None:
    """Diretório vazio: passa validação mas para em discover_docs."""
    with tempfile.TemporaryDirectory() as tmp:
        result = run_agent(tmp)

        assert result["validation_status"] == "valid"
        assert result["discovered_files"] == []
        assert result["final_report"] is None


def test_run_agent_full_flow_with_local_dir() -> None:
    """Fluxo completo com diretório local contendo README.md."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text(
            "# Meu Projeto\n\n"
            "Descrição do projeto com conteúdo suficiente para análise.\n\n"
            "## Instalação\n\npip install meu-projeto\n\n"
            "## Uso\n\nExemplo de uso do projeto aqui com detalhes.\n",
            encoding="utf-8",
        )

        result = run_agent(tmp)

        assert result["validation_status"] == "valid"
        assert len(result["discovered_files"]) >= 1
        assert result["merged_context"] is not None
        assert result["analysis_result"] is not None
        assert result["final_report"] is not None
        assert "Relatório" in result["final_report"]


def test_run_agent_preserves_errors_on_early_stop() -> None:
    """Estado parcial preservado quando fluxo encerra por erro."""
    result = run_agent("")

    # Estado deve ter os campos preservados mesmo com parada antecipada
    assert "validation_status" in result
    assert "validation_message" in result
    assert "errors" in result


def test_run_agent_field_isolation() -> None:
    """Campos não são sobrescritos por nós que não os gerenciam."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text("# Test\n\nConteúdo mínimo suficiente para análise completa do documento.", encoding="utf-8")

        result = run_agent(tmp)

        # raw_input preservado do início ao fim
        assert result["raw_input"] == tmp
        # input_type preservado
        assert result["input_type"] == "path"
