"""Testes para paralelização no grafo LangGraph (fan-out/fan-in).

Valida que:
- Ambos os caminhos paralelos (read_readme, read_prd_docs) executam
- Fan-in (merge_docs) consolida resultados corretamente
- Grafo funciona com apenas um caminho produzindo resultado
- Fluxo completo sequencial + paralelo funciona end-to-end
"""

import tempfile
from pathlib import Path

from app.agent.graph import build_graph, run_agent
from app.agent.nodes.read_readme import read_readme
from app.agent.nodes.read_prd_docs import read_prd_docs
from app.agent.nodes.merge_docs import merge_docs


class TestParallelFanOut:
    """Testes para fan-out: ambos os nós paralelos executam."""

    def test_read_readme_extracts_readme_content(self):
        """read_readme extrai conteúdo de arquivo README."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição do projeto.\n")

            state = {
                "discovered_files": [str(readme)],
                "errors": [],
            }

            result = read_readme(state)

            assert result["readme_content"] is not None
            assert "Projeto" in result["readme_content"]

    def test_read_readme_ignores_non_readme_files(self):
        """read_readme ignora arquivos que não são README."""
        with tempfile.TemporaryDirectory() as tmp:
            prd = Path(tmp) / "PRD.md"
            prd.write_text("# PRD\n\nRequisitos.\n")

            state = {
                "discovered_files": [str(prd)],
                "errors": [],
            }

            result = read_readme(state)

            assert result["readme_content"] is None

    def test_read_prd_docs_extracts_prd_content(self):
        """read_prd_docs extrai conteúdo de arquivo PRD."""
        with tempfile.TemporaryDirectory() as tmp:
            prd = Path(tmp) / "PRD.md"
            prd.write_text("# Product Requirements\n\nRequisitos.\n")

            state = {
                "discovered_files": [str(prd)],
                "errors": [],
            }

            result = read_prd_docs(state)

            assert result["prd_content"] is not None
            assert "Requirements" in result["prd_content"]

    def test_read_prd_docs_ignores_readme_files(self):
        """read_prd_docs ignora arquivos README."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição.\n")

            state = {
                "discovered_files": [str(readme)],
                "errors": [],
            }

            result = read_prd_docs(state)

            assert result["prd_content"] is None

    def test_both_parallel_nodes_execute_with_readme_and_prd(self):
        """Ambos os nós paralelos produzem resultado quando há README e PRD."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição completa do projeto.\n")

            prd = Path(tmp) / "PRD.md"
            prd.write_text("# Product Requirements\n\nRequisitos detalhados.\n")

            files = [str(readme), str(prd)]

            readme_result = read_readme({"discovered_files": files, "errors": []})
            prd_result = read_prd_docs({"discovered_files": files, "errors": []})

            assert readme_result["readme_content"] is not None
            assert prd_result["prd_content"] is not None


class TestParallelFanIn:
    """Testes para fan-in: merge_docs consolida resultados."""

    def test_merge_docs_consolidates_all_files(self):
        """merge_docs gera merged_context com todos os documentos."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# Projeto\n\nDescrição.\n")

            prd = Path(tmp) / "PRD.md"
            prd.write_text("# PRD\n\nRequisitos.\n")

            state = {
                "discovered_files": [str(readme), str(prd)],
                "errors": [],
            }

            result = merge_docs(state)

            assert result["merged_context"] is not None
            assert "README.md" in result["merged_context"]
            assert "PRD.md" in result["merged_context"]

    def test_merge_docs_returns_none_when_no_content(self):
        """merge_docs retorna None quando nenhum conteúdo é lido."""
        with tempfile.TemporaryDirectory() as tmp:
            empty_file = Path(tmp) / "empty.md"
            empty_file.write_text("")

            state = {
                "discovered_files": [str(empty_file)],
                "errors": [],
            }

            result = merge_docs(state)

            assert result["merged_context"] is None
            assert len(result["errors"]) > 0


class TestParallelEndToEnd:
    """Testes end-to-end do grafo com paralelização."""

    def test_full_flow_readme_and_prd_parallel(self):
        """Fluxo completo: README e PRD lidos em paralelo, resultado consolidado."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                "# Meu Projeto\n\n"
                "Descrição completa do projeto.\n\n"
                "## Instalação\n\npip install projeto\n"
            )

            prd = Path(tmp) / "PRD.md"
            prd.write_text(
                "# Product Requirements\n\n"
                "Requisitos detalhados do produto.\n\n"
                "## Features\n\n- Feature A\n"
            )

            result = run_agent(tmp)

            assert result["validation_status"] == "valid"
            assert len(result["discovered_files"]) == 2
            assert result["readme_content"] is not None
            assert result["prd_content"] is not None
            assert result["merged_context"] is not None
            assert result["analysis_result"] is not None
            assert result["final_report"] is not None

    def test_full_flow_only_readme(self):
        """Fluxo completo funciona com apenas README (PRD ausente)."""
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                "# Projeto\n\n"
                "Descrição do projeto com conteúdo suficiente.\n\n"
                "## Uso\n\nExemplo de uso.\n"
            )

            result = run_agent(tmp)

            assert result["readme_content"] is not None
            assert result["prd_content"] is None
            assert result["merged_context"] is not None
            assert result["final_report"] is not None

    def test_full_flow_only_prd(self):
        """Fluxo completo funciona com apenas PRD (README ausente)."""
        with tempfile.TemporaryDirectory() as tmp:
            prd = Path(tmp) / "PRD.md"
            prd.write_text(
                "# Product Requirements\n\n"
                "Requisitos do produto detalhados.\n\n"
                "## Objetivo\n\nDescrever features.\n"
            )

            result = run_agent(tmp)

            assert result["readme_content"] is None
            assert result["prd_content"] is not None
            assert result["merged_context"] is not None
            assert result["final_report"] is not None

    def test_graph_still_has_conditional_routing(self):
        """Grafo mantém roteamento condicional (encerra em validação inválida)."""
        result = run_agent("")

        assert result["validation_status"] == "invalid"
        assert result["discovered_files"] == []
        assert result["merged_context"] is None

    def test_graph_compiles_with_parallel_structure(self):
        """Grafo compila sem erros com a estrutura de paralelização."""
        graph = build_graph()
        assert graph is not None
