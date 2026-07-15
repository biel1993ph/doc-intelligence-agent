"""Nó analyze_docs: avalia qualidade da documentação em 4 dimensões."""

from app.agent.state import AgentState


# Limiar de base insuficiente
MIN_CONTENT_LENGTH = 100
MAX_SCORE_INSUFFICIENT = 3


def analyze_docs(state: AgentState) -> dict:
    """Analisa documentação em 4 dimensões e gera resultado estruturado.

    Dimensões: clareza, cobertura, consistência, onboarding.
    Identifica pontos fortes (1-10) e problemas (1-15).
    Gera nota de 0-10 com justificativa.

    Se base < 100 chars: marca base_insuficiente, nota máxima 3.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com analysis_result e erros.
    """
    merged_context = state.get("merged_context") or ""
    errors = list(state.get("errors", []))

    base_insuficiente = len(merged_context.strip()) < MIN_CONTENT_LENGTH

    # Avaliar dimensões
    dimensions = _evaluate_dimensions(merged_context, base_insuficiente)

    # Identificar pontos fortes e problemas
    strengths = _identify_strengths(merged_context, base_insuficiente)
    issues = _identify_issues(merged_context, base_insuficiente)

    # Reconciliar: remover issues que contradizem strengths
    issues = _reconcile_strengths_and_issues(strengths, issues)

    # Calcular nota
    score, justification = _calculate_score(
        merged_context, dimensions, strengths, issues, base_insuficiente
    )

    analysis_result = {
        "dimensions": dimensions,
        "strengths": strengths,
        "issues": issues,
        "score": score,
        "justification": justification,
        "base_insuficiente": base_insuficiente,
    }

    return {
        "analysis_result": analysis_result,
        "errors": errors,
    }


def _evaluate_dimensions(context: str, insufficient: bool) -> dict:
    """Avalia as 4 dimensões da documentação."""
    if insufficient:
        return {
            "clareza": "não avaliável",
            "cobertura": "não avaliável",
            "consistencia": "não avaliável",
            "onboarding": "não avaliável",
        }

    result = {}

    # Clareza: presença de títulos, parágrafos estruturados
    has_headers = "#" in context
    has_paragraphs = "\n\n" in context
    if has_headers and has_paragraphs:
        result["clareza"] = "adequada"
    elif has_headers or has_paragraphs:
        result["clareza"] = "parcial"
    else:
        result["clareza"] = "insuficiente"

    # Cobertura: presença de seções típicas
    coverage_keywords = ["instalação", "install", "uso", "usage", "api", "contribui", "contributing"]
    found = sum(1 for kw in coverage_keywords if kw in context.lower())
    if found >= 3:
        result["cobertura"] = "ampla"
    elif found >= 1:
        result["cobertura"] = "parcial"
    else:
        result["cobertura"] = "limitada"

    # Consistência: uniformidade de formatação
    lines = context.split("\n")
    header_lines = [l for l in lines if l.startswith("#")]
    if len(header_lines) >= 2:
        result["consistencia"] = "consistente"
    else:
        result["consistencia"] = "parcial"

    # Onboarding: instruções de início rápido
    onboarding_keywords = ["getting started", "quick start", "início", "começar", "run", "executar"]
    if any(kw in context.lower() for kw in onboarding_keywords):
        result["onboarding"] = "presente"
    else:
        result["onboarding"] = "ausente"

    return result


def _identify_strengths(context: str, insufficient: bool) -> list[str]:
    """Identifica pontos fortes da documentação (1-10, ≤280 chars cada)."""
    if insufficient:
        return ["Documentação existente, mesmo que mínima."]

    strengths = []

    if "#" in context:
        strengths.append("Estrutura com cabeçalhos Markdown presente.")

    if "```" in context:
        strengths.append("Exemplos de código incluídos na documentação.")

    if any(kw in context.lower() for kw in ["install", "instalação", "pip", "npm"]):
        strengths.append("Instruções de instalação disponíveis.")

    if any(kw in context.lower() for kw in ["licen", "license", "mit", "apache"]):
        strengths.append("Informação de licença presente.")

    if any(kw in context.lower() for kw in ["contribui", "contributing", "pull request"]):
        strengths.append("Guia de contribuição disponível.")

    if len(context) > 500:
        strengths.append("Documentação com volume adequado de conteúdo.")

    if not strengths:
        strengths.append("Documentação existente.")

    return strengths[:10]


# Mapeamento de categorias para reconciliação strengths vs issues
_CATEGORY_KEYWORDS = {
    "instalação": ["install", "instalação", "pip", "npm", "setup"],
    "licença": ["licen", "license", "mit", "apache"],
    "contribuição": ["contribui", "contributing", "pull request"],
    "código": ["código", "code", "exemplo"],
    "teste": ["test", "teste", "pytest", "jest"],
}


def _reconcile_strengths_and_issues(
    strengths: list[str], issues: list[dict]
) -> list[dict]:
    """Remove issues que contradizem diretamente um strength identificado.

    Se um tópico (ex: licença) aparece como ponto forte, remove a issue
    correspondente que reclama da ausência desse tópico.

    Args:
        strengths: Lista de pontos fortes identificados.
        issues: Lista de problemas identificados.

    Returns:
        Lista de issues filtrada sem contradições.
    """
    # Identificar categorias presentes nos strengths
    strength_text = " ".join(strengths).lower()
    present_categories: set[str] = set()

    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in strength_text for kw in keywords):
            present_categories.add(category)

    # Filtrar issues que reclamam de ausência de algo que já é strength
    filtered_issues = []
    for issue in issues:
        observation = issue.get("observation", "").lower()
        is_contradiction = False

        for category in present_categories:
            keywords = _CATEGORY_KEYWORDS[category]
            if any(kw in observation for kw in keywords):
                # Esta issue reclama de algo que já é ponto forte
                is_contradiction = True
                break

        if not is_contradiction:
            filtered_issues.append(issue)

    # Garantir pelo menos 1 issue
    if not filtered_issues:
        filtered_issues.append({
            "observation": "Documentação aparenta estar completa.",
            "recommendation": "Considerar adicionar exemplos avançados ou FAQ.",
        })

    return filtered_issues


def _has_title(context: str) -> bool:
    """Verifica se o documento inicia com um título de nível 1 nas primeiras 3 linhas."""
    lines = context.strip().splitlines()
    for line in lines[:3]:
        stripped = line.strip()
        if stripped.startswith("# ") and len(stripped) > 2:
            return True
        # Ignorar linhas em branco no início
        if stripped and not stripped.startswith("#"):
            return False
    return False


def _has_description_after_title(context: str) -> bool:
    """Verifica se há parágrafo descritivo nas primeiras 5 linhas após o título."""
    lines = context.strip().splitlines()

    # Encontrar o título
    title_index = -1
    for i, line in enumerate(lines[:3]):
        if line.strip().startswith("# "):
            title_index = i
            break

    if title_index == -1:
        # Sem título, verificar se há texto descritivo no início
        for line in lines[:5]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("-") and len(stripped) > 20:
                return True
        return False

    # Verificar se há parágrafo ANTES do próximo heading (##)
    after_title = lines[title_index + 1: title_index + 6]
    for line in after_title:
        stripped = line.strip()
        # Se encontramos outro heading antes de um parágrafo, não há descrição
        if stripped.startswith("#"):
            return False
        # Parágrafo descritivo: não vazio, não é lista, tem tamanho razoável
        if stripped and not stripped.startswith("-") and not stripped.startswith("|") and len(stripped) > 20:
            return True

    return False


def _identify_issues(context: str, insufficient: bool) -> list[dict]:
    """Identifica problemas na documentação (1-15)."""
    if insufficient:
        return [
            {
                "observation": "Base documental insuficiente (< 100 caracteres).",
                "recommendation": "Expandir documentação com conteúdo descritivo do projeto.",
            }
        ]

    issues = []

    # Verificar título do projeto
    if not _has_title(context):
        issues.append({
            "observation": "Título do projeto ausente.",
            "recommendation": "Adicionar título de nível 1 (# Nome do Projeto) no início do documento.",
        })

    # Verificar descrição/resumo do projeto
    if not _has_description_after_title(context):
        issues.append({
            "observation": "Descrição/resumo do projeto ausente.",
            "recommendation": "Adicionar 1-3 frases descrevendo o propósito do projeto logo após o título.",
        })

    if "```" not in context:
        issues.append({
            "observation": "Ausência de exemplos de código.",
            "recommendation": "Adicionar blocos de código com exemplos de uso.",
        })

    if not any(kw in context.lower() for kw in ["install", "instalação", "pip", "npm", "setup"]):
        issues.append({
            "observation": "Instruções de instalação não encontradas.",
            "recommendation": "Incluir seção de instalação com comandos necessários.",
        })

    if not any(kw in context.lower() for kw in ["api", "endpoint", "função", "function", "método"]):
        issues.append({
            "observation": "Documentação de API/funções não encontrada.",
            "recommendation": "Documentar interfaces públicas e seus parâmetros.",
        })

    if not any(kw in context.lower() for kw in ["contribui", "contributing"]):
        issues.append({
            "observation": "Guia de contribuição ausente.",
            "recommendation": "Adicionar CONTRIBUTING.md ou seção equivalente.",
        })

    if not any(kw in context.lower() for kw in ["licen", "license"]):
        issues.append({
            "observation": "Informação de licença não encontrada.",
            "recommendation": "Incluir arquivo LICENSE ou seção de licenciamento.",
        })

    if not any(kw in context.lower() for kw in ["test", "teste", "pytest", "jest"]):
        issues.append({
            "observation": "Instruções de teste não encontradas.",
            "recommendation": "Documentar como executar os testes do projeto.",
        })

    # Verificações estruturais
    issues.extend(_check_structural_quality(context))

    if not issues:
        issues.append({
            "observation": "Documentação aparenta estar completa.",
            "recommendation": "Considerar adicionar exemplos avançados ou FAQ.",
        })

    return issues[:15]


def _check_structural_quality(context: str) -> list[dict]:
    """Verifica qualidade estrutural do documento.

    Detecta:
    - Seções vazias (heading seguido de outro heading sem conteúdo)
    - Documento longo sem TOC (>5 seções, >30 linhas)
    - Ausência de links
    - Ausência de parágrafos explicativos (só código e cabeçalhos)
    """
    issues = []
    lines = context.splitlines()

    # Detectar seções vazias
    empty_sections = 0
    for i in range(len(lines) - 1):
        if lines[i].strip().startswith("#") and lines[i + 1].strip().startswith("#"):
            empty_sections += 1

    if empty_sections >= 2:
        issues.append({
            "observation": f"Seções vazias detectadas ({empty_sections} cabeçalhos consecutivos sem conteúdo).",
            "recommendation": "Preencher seções vazias ou removê-las do documento.",
        })

    # Detectar documento longo sem TOC
    header_count = sum(1 for l in lines if l.strip().startswith("#"))
    content_lines = len([l for l in lines if l.strip()])
    has_toc_indicator = any(
        kw in context.lower()
        for kw in ["sumário", "índice", "table of contents", "toc", "## conteúdo"]
    )

    if header_count > 5 and content_lines >= 30 and not has_toc_indicator:
        issues.append({
            "observation": "Documento longo sem sumário/Table of Contents.",
            "recommendation": "Adicionar sumário com links para as seções principais.",
        })

    # Detectar ausência de links
    has_links = "](http" in context or "](/" in context or "[" in context and "](" in context
    if not has_links and len(context) > 300:
        issues.append({
            "observation": "Ausência de links ou referências externas.",
            "recommendation": "Incluir links para documentação adicional, repositório ou recursos relacionados.",
        })

    return issues


# Problemas críticos: ausência de título, descrição, instalação
CRITICAL_ISSUE_KEYWORDS = ["título", "descrição", "resumo", "instalação", "install"]
MAX_SCORE_WITH_CRITICAL = 7


def _calculate_score(
    context: str,
    dimensions: dict,
    strengths: list,
    issues: list,
    insufficient: bool,
) -> tuple[int, str]:
    """Calcula nota de 0-10 com justificativa (≥2 frases).

    Regras:
    - Base insuficiente: nota máxima 3
    - Problema crítico presente: nota máxima 7
    - Problemas críticos: ausência de título, descrição, instalação
    - Problemas menores: ausência de contributing, FAQ, exemplos avançados
    """
    if insufficient:
        score = min(2, MAX_SCORE_INSUFFICIENT)
        justification = (
            "Base documental insuficiente para avaliação completa. "
            "A nota foi limitada a no máximo 3 devido ao volume mínimo de conteúdo disponível."
        )
        return score, justification

    # Classificar problemas em críticos e menores
    critical_issues = []
    minor_issues = []
    for issue in issues:
        obs = issue.get("observation", "").lower()
        if any(kw in obs for kw in CRITICAL_ISSUE_KEYWORDS):
            critical_issues.append(issue)
        else:
            minor_issues.append(issue)

    has_critical = len(critical_issues) > 0

    # Calcular score
    base_score = 5
    dim_values = list(dimensions.values())

    # Bonus por dimensões positivas
    positive_dims = ["adequada", "ampla", "consistente", "presente"]
    bonus = sum(1 for v in dim_values if v in positive_dims)

    # Penalidade: críticos pesam 2, menores pesam 1
    penalty = (len(critical_issues) * 2) + len(minor_issues)
    penalty = min(penalty, 6)

    # Bonus por pontos fortes
    strength_bonus = min(len(strengths), 3)

    score = max(0, min(10, base_score + bonus + strength_bonus - penalty))

    # Limitar nota se há problemas críticos
    if has_critical:
        score = min(score, MAX_SCORE_WITH_CRITICAL)

    justification = _build_contextual_justification(
        dimensions, strengths, issues, critical_issues, minor_issues, has_critical, score
    )

    return score, justification


def _build_contextual_justification(
    dimensions: dict,
    strengths: list,
    issues: list,
    critical_issues: list,
    minor_issues: list,
    has_critical: bool,
    score: int,
) -> str:
    """Gera justificativa contextualizada com detalhes por dimensão.

    Menciona ao menos 2 dimensões com explicação, o principal problema
    e o principal ponto forte. Mínimo 3 frases.
    """
    parts = []

    # Frase 1: resumo quantitativo
    parts.append(
        f"Avaliação baseada em {len(strengths)} pontos fortes e {len(issues)} problemas "
        f"({len(critical_issues)} críticos, {len(minor_issues)} menores)."
    )

    # Frase 2-3: detalhes de dimensões
    dim_descriptions = {
        "clareza": {"adequada": "com boa estrutura e formatação", "parcial": "com estrutura parcial", "insuficiente": "com estrutura insuficiente"},
        "cobertura": {"ampla": "cobrindo os tópicos essenciais", "parcial": "com cobertura parcial dos tópicos", "limitada": "com cobertura limitada"},
        "consistencia": {"consistente": "mantendo uniformidade de estilo", "parcial": "com consistência parcial de formatação"},
        "onboarding": {"presente": "facilitando o início para novos desenvolvedores", "ausente": "sem instruções claras de início rápido"},
    }

    dim_phrases = []
    for dim_name, dim_value in dimensions.items():
        descs = dim_descriptions.get(dim_name, {})
        if dim_value in descs:
            dim_phrases.append(f"{dim_name} {descs[dim_value]}")

    if len(dim_phrases) >= 2:
        parts.append(f"A documentação apresenta {dim_phrases[0]} e {dim_phrases[1]}.")
    elif dim_phrases:
        parts.append(f"A documentação apresenta {dim_phrases[0]}.")

    # Frase 4: principal ponto forte
    if strengths and strengths[0] != "Documentação existente.":
        parts.append(f"Destaque positivo: {strengths[0].rstrip('.')}")

    # Frase 5: principal problema
    if issues:
        main_issue = issues[0].get("observation", "")
        if main_issue:
            parts.append(f"Principal ponto de atenção: {main_issue.rstrip('.')}")

    # Frase sobre limitação por problemas críticos
    if has_critical:
        parts.append(
            f"A nota foi limitada a no máximo {MAX_SCORE_WITH_CRITICAL} devido a problemas críticos pendentes."
        )

    return ". ".join(parts) + "."
