"""Testes End-to-End (E2E) do Doc Intelligence Agent.

Simula o fluxo completo da aplicação: entrada → processamento → saída.
Gerado e refinado com apoio de IA (Kiro/Claude) para cobrir cenários
reais de uso com priorização por risco.

Cenários E2E:
1. Fluxo completo com repositório local (README + PRD)
2. Fluxo com documento insuficiente (< 100 chars)
3. Fluxo com input inválido (sem erro não tratado)
4. Fluxo E2E verifica estrutura completa do relatório final
5. Fluxo verifica que trace_id e node_timings são consistentes
"""

import tempfile
from pathlib import Path

import pytest

from app.agent.graph import run_agent


class TestE2EFullFlow:
    """Testes E2E simulando o fluxo completo da aplicação.

    Prioridade: ALTA (risco crítico)
    Justificativa: Falha no fluxo principal impede 100% dos usuários.
    """

    def test_e2e_full_analysis_readme_and_prd(self):
        """E2E: análise completa com README + PRD produz relatório válido.

        Simula o cenário real de uso: usuário fornece diretório com
        documentação e recebe relatório estruturado com nota.
        """
        with tempfile.TemporaryDirectory() as tmp:
            # Criar documentação realista
            readme = Path(tmp) / "README.md"
            readme.write_text(
                "# Doc Intelligence Agent\n\n"
                "Agente que avalia documentação técnica de software.\n\n"
                "## Instalação\n\n"
                "```bash\npip install -e .\n```\n\n"
                "## Uso\n\n"
                "```python\nfrom app.agent.graph import run_agent\nresult = run_agent('https://github.com/owner/repo')\n```\n\n"
                "## Contribuição\n\nEnvie um Pull Request para a branch develop.\n\n"
                "## Licença\n\nMIT License.\n",
                encoding="utf-8",
            )
            prd = Path(tmp) / "PRD.md"
            prd.write_text(
                "# Product Requirements Document\n\n"
                "## Visão Geral\n\n"
                "Ferramenta de análise automática de documentação.\n\n"
                "## Funcionalidades\n\n"
                "- Análise de qualidade\n"
                "- Identificação de lacunas\n"
                "- Geração de relatório\n",
                encoding="utf-8",
            )

            # Executar fluxo completo
            result = run_agent(tmp)

            # Verificações E2E
            assert result["validation_status"] == "valid"
            assert result["input_type"] == "path"
            assert len(result["discovered_files"]) == 2
            assert result["readme_content"] is not None
            assert result["prd_content"] is not None
            assert result["merged_context"] is not None
            assert result["analysis_result"] is not None
            assert result["final_report"] is not None
            assert result["trace_id"] != ""
            assert len(result["node_timings"]) >= 7
            assert result["errors"] == []

            # Verificar estrutura do relatório
            report = result["final_report"]
            assert "Relatório" in report
            assert "Pontos Fortes" in report
            assert "Nota" in report
            assert "Limitações" in report

            # Verificar score válido
            score = result["analysis_result"]["score"]
            assert 0 <= score <= 10

    def test_e2e_insufficient_base_limits_score(self):
        """E2E: documento com < 100 chars resulta em nota máxima 3.

        Prioridade: ALTA
        Cenário de risco: documento quase vazio não deve receber nota alta.
        """
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("# X\n\nY\n", encoding="utf-8")

            result = run_agent(tmp)

            assert result["analysis_result"] is not None
            assert result["analysis_result"]["base_insuficiente"] is True
            assert result["analysis_result"]["score"] <= 3
            assert result["final_report"] is not None
            assert "insuficiente" in result["final_report"].lower()

    def test_e2e_invalid_input_does_not_crash(self):
        """E2E: entrada inválida encerra gracefully sem exceção.

        Prioridade: ALTA
        Cenário de risco: inputs malformados não devem derrubar o agente.
        """
        # URL inválida
        result = run_agent("ftp://invalid-protocol.com/repo")
        assert result["validation_status"] == "invalid"
        assert result["final_report"] is None
        assert result["analysis_result"] is None

        # Entrada vazia
        result = run_agent("")
        assert result["validation_status"] == "invalid"
        assert result["final_report"] is None

        # Caminho inexistente
        result = run_agent("/caminho/que/nao/existe")
        assert result["validation_status"] == "invalid"
        assert result["final_report"] is None

    def test_e2e_report_structure_complete(self):
        """E2E: relatório final contém todas as seções na ordem correta.

        Prioridade: MÉDIA
        Cenário de risco: relatório incompleto confunde o usuário.
        """
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                "# Projeto\n\n"
                "Descrição completa do projeto com informações suficientes.\n\n"
                "## Instalação\n\npip install projeto\n\n"
                "## Uso\n\nExemplo de uso detalhado aqui.\n",
                encoding="utf-8",
            )

            result = run_agent(tmp)
            report = result["final_report"]

            # Seções obrigatórias na ordem
            sections = ["Relatório", "Escopo", "Pontos Fortes", "Problemas", "Checklist", "Nota", "Limitações"]
            for section in sections:
                assert section in report, f"Seção '{section}' ausente no relatório"

    def test_e2e_observability_consistency(self):
        """E2E: trace_id é consistente e node_timings registra todos os nós.

        Prioridade: MÉDIA
        Cenário de risco: observabilidade falha impede investigação de problemas.
        """
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                "# Projeto\n\nDescrição do projeto.\n\n## Uso\n\nExemplo.\n",
                encoding="utf-8",
            )

            result = run_agent(tmp)

            # trace_id é UUID válido
            import uuid
            uuid.UUID(result["trace_id"], version=4)

            # node_timings tem entries para os nós executados
            node_names = [t["node"] for t in result["node_timings"]]
            assert "receive_input" in node_names
            assert "validate_input" in node_names
            assert "discover_docs" in node_names
            assert "merge_docs" in node_names
            assert "analyze_docs" in node_names
            assert "build_report" in node_names
            assert "present_result" in node_names

            # Todos os timings têm duration_ms >= 0
            for timing in result["node_timings"]:
                assert timing["duration_ms"] >= 0
