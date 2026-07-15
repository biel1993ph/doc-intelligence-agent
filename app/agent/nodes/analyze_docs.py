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

    if not issues:
        issues.append({
            "observation": "Documentação aparenta estar completa.",
            "recommendation": "Considerar adicionar exemplos avançados ou FAQ.",
        })

    return issues[:15]


def _calculate_score(
    context: str,
    dimensions: dict,
    strengths: list,
    issues: list,
    insufficient: bool,
) -> tuple[int, str]:
    """Calcula nota de 0-10 com justificativa (≥2 frases)."""
    if insufficient:
        score = min(2, MAX_SCORE_INSUFFICIENT)
        justification = (
            "Base documental insuficiente para avaliação completa. "
            "A nota foi limitada a no máximo 3 devido ao volume mínimo de conteúdo disponível."
        )
        return score, justification

    # Calcular score baseado em dimensões e balanço fortes/problemas
    base_score = 5
    dim_values = list(dimensions.values())

    # Bonus por dimensões positivas
    positive_dims = ["adequada", "ampla", "consistente", "presente"]
    bonus = sum(1 for v in dim_values if v in positive_dims)

    # Penalidade por problemas
    penalty = min(len(issues), 4)

    # Bonus por pontos fortes
    strength_bonus = min(len(strengths), 3)

    score = max(0, min(10, base_score + bonus + strength_bonus - penalty))

    justification = (
        f"Avaliação baseada em {len(strengths)} pontos fortes e {len(issues)} problemas identificados. "
        f"As dimensões de clareza, cobertura, consistência e onboarding foram consideradas na composição da nota."
    )

    return score, justification
