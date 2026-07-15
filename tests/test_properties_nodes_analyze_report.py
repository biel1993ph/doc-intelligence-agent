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
    """Nota entre 0-10, justificativa >= 3 frases."""
    context = "# README\n\nDescrição completa do projeto com informações relevantes para avaliação completa das dimensões e nota final."
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    assert 0 <= ar["score"] <= 10
    # Justificativa com pelo menos 3 frases (3 pontos)
    sentences = [s.strip() for s in ar["justification"].split(".") if s.strip()]
    assert len(sentences) >= 3


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


# --- Verificação de título e descrição (#44) ---


def test_analyze_docs_detects_missing_title() -> None:
    """Documento sem título # nas primeiras linhas gera issue de título ausente."""
    # Conteúdo sem título, começa com texto normal mas suficiente para análise
    context = (
        "**Dois perfis de uso:**\n"
        "- Participante: Interface simples e intuitiva para responder pesquisas em totens\n"
        "- Master: Acesso protegido por senha para configurar eventos, visualizar feedbacks\n\n"
        "## Tecnologias\n\n"
        "| Tecnologia | Versão | Uso |\n"
        "| Flutter | 3.x | Framework principal |\n"
        "| Dart | 3.11 | Linguagem |\n\n"
        "## Instalação\n\npip install projeto\n\n"
        "## Uso\n\nExemplo de uso detalhado aqui com informações relevantes.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"] for i in issues]
    assert any("Título" in obs and "ausente" in obs for obs in observations), (
        f"Esperava issue de título ausente, mas encontrou: {observations}"
    )


def test_analyze_docs_detects_missing_description() -> None:
    """Documento com título mas sem descrição gera issue de descrição ausente."""
    # Título seguido imediatamente de outro heading sem descrição
    context = (
        "# Meu Projeto\n\n"
        "## Instalação\n\n"
        "pip install projeto com todas as dependências necessárias para o ambiente de produção\n\n"
        "## Uso\n\nExemplo de uso aqui com detalhes suficientes para o leitor entender como funciona.\n\n"
        "## Contribuindo\n\nFaça um fork e envie pull request com suas alterações documentadas.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"] for i in issues]
    assert any("Descrição" in obs or "resumo" in obs for obs in observations), (
        f"Esperava issue de descrição ausente, mas encontrou: {observations}"
    )


def test_analyze_docs_no_title_issue_when_title_present() -> None:
    """Documento com título válido NÃO gera issue de título ausente."""
    context = (
        "# TaskFlow\n\n"
        "Gerenciador de tarefas colaborativo com interface web.\n\n"
        "## Instalação\n\npip install taskflow\n\n"
        "## Uso\n\nExemplo aqui.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"] for i in issues]
    assert not any("Título" in obs and "ausente" in obs for obs in observations)


def test_analyze_docs_no_description_issue_when_description_present() -> None:
    """Documento com título e descrição NÃO gera issue de descrição ausente."""
    context = (
        "# TaskFlow\n\n"
        "Gerenciador de tarefas colaborativo com interface web e API REST.\n\n"
        "## Instalação\n\npip install taskflow\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"] for i in issues]
    assert not any("Descrição" in obs and "ausente" in obs for obs in observations)


# --- Reconciliação strengths vs issues (#45) ---


def test_no_contradiction_license() -> None:
    """Se licença é ponto forte, não deve aparecer como problema."""
    context = (
        "# Projeto\n\n"
        "Descrição do projeto com informações suficientes.\n\n"
        "## Licença\n\nMIT License\n\n"
        "## Instalação\n\npip install projeto\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    strength_text = " ".join(ar["strengths"]).lower()
    assert "licen" in strength_text or "license" in strength_text

    issue_observations = [i["observation"].lower() for i in ar["issues"]]
    assert not any("licen" in obs for obs in issue_observations), (
        f"Contradição: licença é ponto forte mas também aparece como problema: {issue_observations}"
    )


def test_no_contradiction_install() -> None:
    """Se instalação é ponto forte, não deve aparecer como problema."""
    context = (
        "# Projeto\n\n"
        "Descrição do projeto aqui com detalhes.\n\n"
        "## Instalação\n\npip install projeto\n\n"
        "## Uso\n\nExemplo de uso com detalhes.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    issue_observations = [i["observation"].lower() for i in ar["issues"]]
    assert not any("install" in obs and "não encontrad" in obs for obs in issue_observations)


def test_no_contradiction_contributing() -> None:
    """Se contribuição é ponto forte, não deve aparecer como problema."""
    context = (
        "# Projeto\n\n"
        "Descrição completa do projeto com detalhes.\n\n"
        "## Contributing\n\nFaça fork e envie PR.\n\n"
        "## Instalação\n\npip install x\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    issue_observations = [i["observation"].lower() for i in ar["issues"]]
    assert not any("contribui" in obs and "ausente" in obs for obs in issue_observations)


# --- Nota com pesos (#46) ---


def test_score_limited_with_critical_issue_missing_title() -> None:
    """Nota máxima 7 quando título está ausente (problema crítico)."""
    # README sem título — começa com texto direto
    context = (
        "**Dois perfis de uso:**\n"
        "- Participante: Interface simples para responder pesquisas\n"
        "- Master: Acesso protegido por senha para configurar eventos\n\n"
        "## Instalação\n\npip install projeto\n\n"
        "## Uso\n\nExemplo de uso aqui.\n\n"
        "## Contributing\n\nFork e PR.\n\n"
        "## Licença\n\nMIT License.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    assert ar["score"] <= 7, f"Nota deveria ser <= 7 com título ausente, mas foi {ar['score']}"


def test_score_limited_with_critical_issue_missing_description() -> None:
    """Nota máxima 7 quando descrição está ausente (problema crítico)."""
    # README com título mas sem descrição (heading direto)
    context = (
        "# Projeto\n\n"
        "## Instalação\n\npip install projeto com dependências completas\n\n"
        "## Uso\n\nExemplo detalhado de uso com mais texto para preencher o conteúdo.\n\n"
        "## Contributing\n\nFaça fork.\n\n"
        "## Licença\n\nMIT.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    assert ar["score"] <= 7, f"Nota deveria ser <= 7 sem descrição, mas foi {ar['score']}"


def test_score_can_exceed_7_without_critical_issues() -> None:
    """Nota pode ser > 7 quando não há problemas críticos."""
    context = (
        "# TaskFlow\n\n"
        "Gerenciador de tarefas colaborativo com interface web e API REST completa.\n\n"
        "## Instalação\n\npip install taskflow\n\n"
        "```bash\npip install taskflow\n```\n\n"
        "## Uso\n\nExemplo de uso:\n\n```python\nimport taskflow\n```\n\n"
        "## API\n\nEndpoint principal: /api/tasks\n\n"
        "## Contributing\n\nFork e PR.\n\n"
        "## Licença\n\nMIT License\n\n"
        "## Testes\n\npytest tests/\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    ar = result["analysis_result"]
    # Verificar que não há problemas críticos
    critical_kws = ["título", "descrição", "resumo", "instalação", "install"]
    has_critical = any(
        any(kw in i["observation"].lower() for kw in critical_kws)
        for i in ar["issues"]
    )
    if not has_critical:
        assert ar["score"] >= 7, f"Nota deveria ser >= 7 sem problemas críticos, mas foi {ar['score']}"


# --- Verificações estruturais (#47) ---


def test_detects_empty_sections() -> None:
    """Detecta seções vazias (headings consecutivos sem conteúdo)."""
    context = (
        "# Projeto\n\n"
        "Descrição do projeto com conteúdo suficiente.\n\n"
        "## Seção 1\n"
        "## Seção 2\n"
        "## Seção 3\n\n"
        "Conteúdo aqui.\n\n"
        "## Instalação\n\npip install x\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"].lower() for i in issues]
    assert any("seções vazias" in obs or "vazias" in obs for obs in observations)


def test_detects_long_doc_without_toc() -> None:
    """Detecta documento longo (>5 seções) sem sumário."""
    sections = "\n\n".join([
        "# Projeto\n\nDescrição completa do projeto com informações detalhadas.",
        "## Seção 1\n\nConteúdo detalhado da seção 1 com múltiplas linhas.\nLinha extra de conteúdo.\nMais detalhes aqui.",
        "## Seção 2\n\nConteúdo detalhado da seção 2 com explicações.\nOutra linha.\nMais informações.",
        "## Seção 3\n\nConteúdo da seção 3 com exemplos.\nDetalhes adicionais.\nTexto complementar.",
        "## Seção 4\n\nConteúdo da seção 4 descritivo.\nMais texto aqui.\nInformações extras.",
        "## Seção 5\n\nConteúdo da seção 5 com documentação.\nDetalhes.\nMais coisas.",
        "## Seção 6\n\nConteúdo da seção 6 final.\nTexto adicional.\nÚltima linha.",
        "## Instalação\n\npip install projeto\nComando adicional aqui.\nMais instruções.",
    ])
    state = _make_state(merged_context=sections)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"].lower() for i in issues]
    assert any("sumário" in obs or "table of contents" in obs for obs in observations)


def test_no_toc_issue_for_short_doc() -> None:
    """Documento curto (<5 seções) não gera issue de TOC."""
    context = (
        "# Projeto\n\nDescrição do projeto.\n\n"
        "## Instalação\n\npip install x\n\n"
        "## Uso\n\nExemplo aqui.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"].lower() for i in issues]
    assert not any("sumário" in obs or "table of contents" in obs for obs in observations)


# --- Justificativa contextualizada (#48) ---


def test_justification_mentions_dimensions() -> None:
    """Justificativa menciona ao menos uma dimensão com explicação."""
    context = (
        "# Projeto\n\n"
        "Descrição do projeto com informações suficientes para avaliação.\n\n"
        "## Instalação\n\npip install projeto\n\n"
        "## Uso\n\nExemplo aqui.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    justification = result["analysis_result"]["justification"].lower()
    dimension_keywords = ["clareza", "cobertura", "consistencia", "consistência", "onboarding"]
    assert any(kw in justification for kw in dimension_keywords), (
        f"Justificativa deveria mencionar dimensões: {justification}"
    )


def test_justification_mentions_main_issue() -> None:
    """Justificativa menciona o principal problema encontrado."""
    context = (
        "# Projeto\n\n"
        "Descrição do projeto aqui com detalhes suficientes para análise completa de todas dimensões.\n\n"
        "## Uso\n\nExemplo de uso com mais texto para passar do limite mínimo de caracteres.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    justification = result["analysis_result"]["justification"].lower()
    assert "ponto de atenção" in justification or "problema" in justification


def test_justification_minimum_3_sentences() -> None:
    """Justificativa tem no mínimo 3 frases."""
    context = (
        "# Projeto\n\n"
        "Um projeto interessante com funcionalidades úteis.\n\n"
        "## Instalação\n\npip install x\n\n"
        "## Contributing\n\nFaça fork.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    justification = result["analysis_result"]["justification"]
    sentences = [s.strip() for s in justification.split(".") if s.strip()]
    assert len(sentences) >= 3, f"Apenas {len(sentences)} frases: {justification}"


# --- Fix: título com headers de rastreabilidade ---


def test_title_detected_with_traceability_header() -> None:
    """Título é detectado mesmo quando merged_context começa com header de rastreabilidade."""
    context = (
        "--- Fonte: README.md ---\n\n"
        "# LeadImob\n\n"
        "Sistema de gerenciamento imobiliário com funcionalidades completas para gestão de leads.\n\n"
        "## Instalação\n\npip install leadimob\n\n"
        "## Uso\n\nExemplo de uso aqui com detalhes.\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"] for i in issues]
    assert not any("Título" in obs and "ausente" in obs for obs in observations), (
        f"Título presente mas detectado como ausente. Issues: {observations}"
    )


def test_description_detected_with_traceability_header() -> None:
    """Descrição é detectada mesmo com header de rastreabilidade antes do conteúdo."""
    context = (
        "--- Fonte: README.md ---\n\n"
        "# MeuProjeto\n\n"
        "Uma aplicação completa para gerenciar tarefas com interface moderna.\n\n"
        "## Instalação\n\npip install meuprojeto\n"
    )
    state = _make_state(merged_context=context)
    result = analyze_docs(state)

    issues = result["analysis_result"]["issues"]
    observations = [i["observation"] for i in issues]
    assert not any("Descrição" in obs and "ausente" in obs for obs in observations), (
        f"Descrição presente mas detectada como ausente. Issues: {observations}"
    )
