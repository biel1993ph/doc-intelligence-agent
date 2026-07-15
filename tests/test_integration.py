"""Testes de integração: fluxo completo do agente."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from app.agent.graph import run_agent


def test_full_flow_local_readme(local_dir_with_readme: Path) -> None:
    """Fluxo completo com diretório local contendo README.md."""
    result = run_agent(str(local_dir_with_readme))

    assert result["validation_status"] == "valid"
    assert result["input_type"] == "path"
    assert len(result["discovered_files"]) >= 1
    assert result["readme_content"] is not None
    assert result["merged_context"] is not None
    assert result["analysis_result"] is not None
    assert result["final_report"] is not None
    assert "Relatório" in result["final_report"]


def test_full_flow_local_readme_and_prd(local_dir_with_readme_and_prd: Path) -> None:
    """Fluxo completo com README.md e PRD.md."""
    result = run_agent(str(local_dir_with_readme_and_prd))

    assert result["validation_status"] == "valid"
    assert result["readme_content"] is not None
    assert result["prd_content"] is not None
    assert result["merged_context"] is not None
    assert "README.md" in result["merged_context"]
    assert result["final_report"] is not None


def test_full_flow_with_md_files_upload() -> None:
    """Fluxo com upload de arquivos .md (simulado como diretório)."""
    with tempfile.TemporaryDirectory() as tmp:
        # Simular upload: criar arquivos .md no diretório
        readme = Path(tmp) / "README.md"
        readme.write_text(
            "# Upload Test\n\nConteúdo suficiente para avaliação completa do documento.\n\n"
            "## Seção\n\nDetalhes aqui.\n",
            encoding="utf-8",
        )

        result = run_agent(tmp)

        assert result["validation_status"] == "valid"
        assert result["final_report"] is not None


def test_flow_stops_at_invalid_validation() -> None:
    """Fluxo interrompido por validação inválida."""
    # URL com esquema inválido
    result = run_agent("ftp://invalid-scheme.com/repo")

    assert result["validation_status"] == "invalid"
    assert result["discovered_files"] == []
    assert result["merged_context"] is None
    assert result["final_report"] is None


def test_flow_stops_at_empty_input() -> None:
    """Fluxo interrompido com entrada vazia."""
    result = run_agent("")

    assert result["validation_status"] == "invalid"
    assert result["input_type"] == "empty"
    assert result["final_report"] is None


def test_flow_stops_at_empty_directory() -> None:
    """Fluxo interrompido com diretório vazio (sem documentos)."""
    with tempfile.TemporaryDirectory() as tmp:
        result = run_agent(tmp)

        assert result["validation_status"] == "valid"
        assert result["discovered_files"] == []
        assert result["final_report"] is None


def test_flow_preserves_state_on_early_stop() -> None:
    """Estado parcial preservado quando fluxo encerra antecipadamente."""
    result = run_agent("http://")

    assert result["raw_input"] == "http://"
    assert result["input_type"] == "url"
    assert result["validation_status"] == "invalid"
    assert "errors" in result


def test_clone_timeout_simulated() -> None:
    """Timeout de clonagem simulado com mock."""
    with patch(
        "app.agent.nodes.validate_input.validate_repository_url",
        return_value=(True, "URL válida e acessível."),
    ):
        with patch(
            "app.agent.nodes.discover_docs.clone_or_open_repository",
            return_value=("", "Falha na clonagem: timeout"),
        ):
            result = run_agent("https://github.com/example/repo")

            # Deve ter falhado na descoberta (clone falhou)
            assert result["discovered_files"] == []
            assert len(result.get("errors", [])) > 0
