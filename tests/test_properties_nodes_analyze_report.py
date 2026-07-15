"""Testes de propriedade para nós analyze_docs, build_report e report_service."""

import tempfile
from pathlib import Path

from hypothesis import given, strategies as st, settings

from app.agent.nodes.analyze_docs import analyze_docs, MIN_CONTENT_LENGTH, MAX_SCORE_INSUFFICIENT
from app.agent.nodes.build_report import build_report
from app.agent.nodes.present_result import present_result
from app.services.report_service import generate_report_markdown, REPORT_SECTIONS_ORDER


def _make_state(**kwargs) -> dict:
    """Cria estado mínimo para testes."""
    defaults = {
        "raw_input": "",
        "input_type": "",
        "validation_status": "",
        "validation_message": "",
        "repository_url": None,
        "local_files": [],
        "discovered_files": [],
        "readme_content": None,
        "prd_content": None,
        "merged_context": None,
        "analysis_result": None,
        "final_report": None,
        "errors": [],
    }
    defaults.update(kwargs)
    return defaults


# --- analyze_docs: estrutura do resultado ---


def test_analyze_docs_result_structure() -> None:
    """analysis_result contém todas as chaves obrigatórias."""
    context = "# README\n\nEste projeto faz algo interessante.\n\n## Instalação\n\npip install projeto\n\n## Uso\n\nExemplo de uso aqui."
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    assert "dimensions" in ar
    assert "strengths" in ar
    assert "issues" in ar
    assert "score" in ar
    assert "justification" in ar
    assert "base_insuficiente" in ar


def test_analyze_docs_dimensions_has_four_keys() -> None:
    """Dimensões contém exatamente 4 chaves."""
    context = "# Projeto\n\nDescrição do projeto com conteúdo suficiente para avaliação completa das dimensões."
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    dims = result["analysis_result"]["dimensions"]
    assert len(dims) == 4
    assert "clareza" in dims
    assert "cobertura" in dims
    assert "consistencia" in dims
    assert "onboarding" in dims


# --- analyze_docs: base insuficiente ---


@given(
    text=st.text(min_size=0, max_size=MIN_CONTENT_LENGTH - 1),
)
@settings(max_examples=50)
def test_analyze_docs_insufficient_base_limits_score(text: str) -> None:
    """Base < 100 chars: base_insuficiente=True, nota <= 3."""
    state = _make_state(merged_context=text)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    assert ar["base_insuficiente"] is True
    assert ar["score"] <= MAX_SCORE_INSUFFICIENT


def test_analyze_docs_insufficient_dimensions_not_evaluable() -> None:
    """Base insuficiente: dimensões = 'não avaliável'."""
    state = _make_state(merged_context="curto")
    result = analyze_docs(state)

    dims = result["analysis_result"]["dimensions"]
    for val in dims.values():
        assert val == "não avaliável"


# --- analyze_docs: pontos fortes e problemas ---


def test_analyze_docs_strengths_bounded() -> None:
    """Pontos fortes entre 1 e 10."""
    context = "# README\n\nDescrição.\n\n## Instalação\n\npip install x\n\n```python\nprint('hello')\n```\n\n## Contribuindo\n\nFaça PR.\n\n## Licença\n\nMIT"
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    strengths = result["analysis_result"]["strengths"]
    assert 1 <= len(strengths) <= 10
    for s in strengths:
        assert len(s) <= 280


def test_analyze_docs_issues_bounded() -> None:
    """Problemas entre 1 e 15."""
    context = "# Projeto\n\nApenas uma descrição básica sem muitos detalhes adicionais para o projeto."
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    assert 1 <= len(issues) <= 15
    for issue in issues:
        assert "observation" in issue
        assert "recommendation" in issue


# --- analyze_docs: nota e justificativa ---


def test_analyze_docs_score_range_and_justification() -> None:
    """Nota entre 0-10, justificativa >= 2 frases."""
    context = "# README\n\nDescrição completa do projeto com informações relevantes para avaliação."
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    assert 0 <= ar["score"] <= 10
    # Justificativa com pelo menos 2 frases (2 pontos)
    sentences = [s.strip() for s in ar["justification"].split(".") if s.strip()]
    assert len(sentences) >= 2


# --- generate_report_markdown: 7 seções ---


def test_report_has_all_sections() -> None:
    """Relatório contém todas as 7 seções na ordem correta."""
    analysis = {
        "dimensions": {"clareza": "adequada", "cobertura": "parcial", "consistencia": "consistente", "onboarding": "presente"},
        "strengths": ["Estrutura presente."],
        "issues": [{"observation": "Falta exemplos.", "recommendation": "Adicionar exemplos."}],
        "score": 7,
        "justification": "Boa documentação. Pode melhorar em exemplos.",
        "base_insuficiente": False,
    }

    report = generate_report_markdown(analysis, ["README.md", "PRD.md"])

    assert "# Relatório de Análise de Documentação" in report
    assert "## Escopo" in report
    assert "## Pontos Fortes" in report
    assert "## Problemas Identificados" in report
    assert "## Checklist de Melhorias" in report
    assert "## Nota" in report
    assert "## Limitações" in report


def test_report_sections_order() -> None:
    """Seções do relatório aparecem na ordem definida."""
    analysis = {
        "dimensions": {"clareza": "adequada", "cobertura": "parcial", "consistencia": "parcial", "onboarding": "ausente"},
        "strengths": ["Existe."],
        "issues": [{"observation": "Prob.", "recommendation": "Fix."}],
        "score": 5,
        "justification": "Média. Precisa melhorar.",
        "base_insuficiente": False,
    }

    report = generate_report_markdown(analysis)

    # Verificar que as seções estão em ordem
    pos_escopo = report.find("## Escopo")
    pos_fortes = report.find("## Pontos Fortes")
    pos_problemas = report.find("## Problemas Identificados")
    pos_checklist = report.find("## Checklist")
    pos_nota = report.find("## Nota")
    pos_limitacoes = report.find("## Limitações")

    assert pos_escopo < pos_fortes < pos_problemas < pos_checklist < pos_nota < pos_limitacoes


# --- build_report ---


def test_build_report_without_analysis_errors() -> None:
    """build_report sem analysis_result registra erro."""
    state = _make_state(analysis_result=None)
    result = build_report(state)

    assert result["final_report"] is None
    assert any(e["node"] == "build_report" for e in result["errors"])


def test_build_report_generates_report() -> None:
    """build_report com analysis_result gera final_report."""
    analysis = {
        "dimensions": {"clareza": "adequada", "cobertura": "parcial", "consistencia": "parcial", "onboarding": "ausente"},
        "strengths": ["OK."],
        "issues": [{"observation": "X.", "recommendation": "Y."}],
        "score": 6,
        "justification": "Razoável. Pode melhorar.",
        "base_insuficiente": False,
    }
    state = _make_state(analysis_result=analysis, discovered_files=["README.md"])
    result = build_report(state)

    assert result["final_report"] is not None
    assert "Relatório" in result["final_report"]


# --- present_result ---


def test_present_result_does_not_alter_state() -> None:
    """present_result retorna dict vazio."""
    state = _make_state(final_report="# Report")
    result = present_result(state)
    assert result == {}
