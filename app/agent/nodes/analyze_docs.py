"""Nó analyze_docs: avalia qualidade da documentação em 4 dimensões.

Integra chamada a LLM utilizando o prompt de app/prompts/analysis_prompt.md.
Se a LLM estiver indisponível (sem API key, timeout, erro de parsing),
faz fallback para análise heurística determinística.
"""

import json
import logging
import os
from pathlib import Path

from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

# Limiar de base insuficiente
MIN_CONTENT_LENGTH = 100
MAX_SCORE_INSUFFICIENT = 3

# Timeout para chamada LLM (segundos)
LLM_TIMEOUT = 60

# Caminho do prompt
_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "analysis_prompt.md"


def analyze_docs(state: AgentState) -> dict:
    """Analisa documentação em 4 dimensões e gera resultado estruturado.

    Fluxo:
    1. Tenta análise via LLM (decisão qualitativa do modelo).
    2. Se LLM falhar, faz fallback para análise heurística (regras determinísticas).

    A separação é clara: LLM decide a avaliação qualitativa,
    regras determinísticas validam formato e limites.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com analysis_result e erros.
    """
    merged_context = state.get("merged_context") or ""
    errors: list[dict] = []

    # Tentar análise via LLM
    llm_result = _try_llm_analysis(merged_context)

    if llm_result is not None:
        # Validar formato/limites com regras determinísticas
        analysis_result = _validate_and_normalize(llm_result, merged_context)
        logger.info("Análise realizada via LLM com sucesso.")
    else:
        # Fallback para análise heurística
        logger.warning("LLM indisponível, utilizando análise heurística como fallback.")
        analysis_result = _heuristic_analysis(merged_context)

    return {
        "analysis_result": analysis_result,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Integração LLM
# ---------------------------------------------------------------------------


def _load_prompt() -> str:
    """Carrega o prompt de análise do arquivo markdown."""
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        logger.error("Falha ao carregar prompt: %s", e)
        return ""


def _try_llm_analysis(context: str) -> dict | None:
    """Tenta realizar análise via LLM.

    Retorna o dict parseado da resposta ou None se qualquer etapa falhar.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()

    if not api_key or not model:
        logger.info("OPENAI_API_KEY ou LLM_MODEL não configurados. Pulando LLM.")
        return None

    prompt_template = _load_prompt()
    if not prompt_template:
        return None

    # Montar mensagens
    system_message = prompt_template
    user_message = f"Analise a seguinte documentação:\n\n{context}"

    try:
        # Configurar cliente com base_url opcional (para provedores compatíveis)
        client_kwargs: dict = {
            "api_key": api_key,
            "timeout": LLM_TIMEOUT,
        }
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAI(**client_kwargs)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content or ""
        return _parse_llm_response(raw_content)

    except (APIConnectionError, APITimeoutError, RateLimitError) as e:
        logger.warning("Erro de API LLM: %s", type(e).__name__)
        return None
    except Exception as e:
        logger.warning("Erro inesperado na chamada LLM: %s", e)
        return None


def _parse_llm_response(raw: str) -> dict | None:
    """Parseia e valida a resposta JSON do LLM.

    Retorna o dict se válido, None caso contrário.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Resposta do LLM não é JSON válido: %s", e)
        return None

    # Validar campos obrigatórios
    required_keys = {"dimensions", "strengths", "issues", "score", "justification"}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys())
        logger.warning("Resposta do LLM faltando campos: %s", missing)
        return None

    # Validar tipos básicos
    if not isinstance(data.get("dimensions"), dict):
        return None
    if not isinstance(data.get("strengths"), list):
        return None
    if not isinstance(data.get("issues"), list):
        return None
    if not isinstance(data.get("score"), (int, float)):
        return None
    if not isinstance(data.get("justification"), str):
        return None

    return data


def _validate_and_normalize(llm_result: dict, context: str) -> dict:
    """Aplica regras determinísticas de validação sobre o resultado do LLM.

    Garante que limites e formatos estão corretos independente do LLM.
    """
    base_insuficiente = len(context.strip()) < MIN_CONTENT_LENGTH

    # Normalizar score dentro dos limites
    score = int(llm_result.get("score", 5))
    score = max(0, min(10, score))

    if base_insuficiente:
        score = min(score, MAX_SCORE_INSUFFICIENT)

    # Garantir que strengths tem 1-10 itens
    strengths = llm_result.get("strengths", [])[:10]
    if not strengths:
        strengths = ["Documentação existente."]

    # Garantir que issues tem 1-15 itens
    issues = llm_result.get("issues", [])[:15]
    if not issues:
        issues = [{"observation": "Nenhum problema crítico identificado.", "recommendation": "Manter padrão atual."}]

    # Garantir justification tem pelo menos 2 frases
    justification = llm_result.get("justification", "")
    if justification.count(".") < 2:
        justification += " Avaliação realizada por modelo de linguagem."

    return {
        "dimensions": llm_result.get("dimensions", {}),
        "strengths": strengths,
        "issues": issues,
        "score": score,
        "justification": justification,
        "base_insuficiente": base_insuficiente,
    }


# ---------------------------------------------------------------------------
# Análise heurística (fallback determinístico)
# ---------------------------------------------------------------------------


def _heuristic_analysis(context: str) -> dict:
    """Análise puramente heurística como fallback quando LLM indisponível."""
    base_insuficiente = len(context.strip()) < MIN_CONTENT_LENGTH

    dimensions = _evaluate_dimensions(context, base_insuficiente)
    strengths = _identify_strengths(context, base_insuficiente)
    issues = _identify_issues(context, base_insuficiente)
    issues = _reconcile_strengths_and_issues(strengths, issues)
    score, justification = _calculate_score(
        context, dimensions, strengths, issues, base_insuficiente
    )

    return {
        "dimensions": dimensions,
        "strengths": strengths,
        "issues": issues,
        "score": score,
        "justification": justification,
        "base_insuficiente": base_insuficiente,
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
    header_lines = [line for line in lines if line.startswith("#")]
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
    """Remove issues que contradizem diretamente um strength identificado."""
    strength_text = " ".join(strengths).lower()
    present_categories: set[str] = set()

    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in strength_text for kw in keywords):
            present_categories.add(category)

    filtered_issues = []
    for issue in issues:
        observation = issue.get("observation", "").lower()
        is_contradiction = False

        for category in present_categories:
            keywords = _CATEGORY_KEYWORDS[category]
            if any(kw in observation for kw in keywords):
                is_contradiction = True
                break

        if not is_contradiction:
            filtered_issues.append(issue)

    if not filtered_issues:
        filtered_issues.append({
            "observation": "Documentação aparenta estar completa.",
            "recommendation": "Considerar adicionar exemplos avançados ou FAQ.",
        })

    return filtered_issues


def _strip_traceability_headers(context: str) -> str:
    """Remove headers de rastreabilidade (--- Fonte: ... ---) do início do contexto."""
    lines = context.strip().splitlines()
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("--- Fonte:") and stripped.endswith("---"):
            start = i + 1
            continue
        if stripped == "" and i == start:
            start = i + 1
            continue
        break

    return "\n".join(lines[start:])


def _has_title(context: str) -> bool:
    """Verifica se o documento inicia com um título de nível 1 nas primeiras 3 linhas."""
    clean = _strip_traceability_headers(context)
    lines = clean.strip().splitlines()
    for line in lines[:3]:
        stripped = line.strip()
        if stripped.startswith("# ") and len(stripped) > 2:
            return True
        if stripped and not stripped.startswith("#"):
            return False
    return False


def _has_description_after_title(context: str) -> bool:
    """Verifica se há parágrafo descritivo nas primeiras 5 linhas após o título."""
    clean = _strip_traceability_headers(context)
    lines = clean.strip().splitlines()

    title_index = -1
    for i, line in enumerate(lines[:3]):
        if line.strip().startswith("# "):
            title_index = i
            break

    if title_index == -1:
        for line in lines[:5]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("-") and len(stripped) > 20:
                return True
        return False

    after_title = lines[title_index + 1: title_index + 6]
    for line in after_title:
        stripped = line.strip()
        if stripped.startswith("#"):
            return False
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

    if not _has_title(context):
        issues.append({
            "observation": "Título do projeto ausente.",
            "recommendation": "Adicionar título de nível 1 (# Nome do Projeto) no início do documento.",
        })

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

    issues.extend(_check_structural_quality(context))

    if not issues:
        issues.append({
            "observation": "Documentação aparenta estar completa.",
            "recommendation": "Considerar adicionar exemplos avançados ou FAQ.",
        })

    return issues[:15]


def _check_structural_quality(context: str) -> list[dict]:
    """Verifica qualidade estrutural do documento."""
    issues = []
    lines = context.splitlines()

    empty_sections = 0
    for i in range(len(lines) - 1):
        if lines[i].strip().startswith("#") and lines[i + 1].strip().startswith("#"):
            empty_sections += 1

    if empty_sections >= 2:
        issues.append({
            "observation": f"Seções vazias detectadas ({empty_sections} cabeçalhos consecutivos sem conteúdo).",
            "recommendation": "Preencher seções vazias ou removê-las do documento.",
        })

    header_count = sum(1 for line in lines if line.strip().startswith("#"))
    content_lines = len([line for line in lines if line.strip()])
    has_toc_indicator = any(
        kw in context.lower()
        for kw in ["sumário", "índice", "table of contents", "toc", "## conteúdo"]
    )

    if header_count > 5 and content_lines >= 30 and not has_toc_indicator:
        issues.append({
            "observation": "Documento longo sem sumário/Table of Contents.",
            "recommendation": "Adicionar sumário com links para as seções principais.",
        })

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
    """Calcula nota de 0-10 com justificativa (≥2 frases)."""
    if insufficient:
        score = min(2, MAX_SCORE_INSUFFICIENT)
        justification = (
            "Base documental insuficiente para avaliação completa. "
            "A nota foi limitada a no máximo 3 devido ao volume mínimo de conteúdo disponível."
        )
        return score, justification

    critical_issues = []
    minor_issues = []
    for issue in issues:
        obs = issue.get("observation", "").lower()
        if any(kw in obs for kw in CRITICAL_ISSUE_KEYWORDS):
            critical_issues.append(issue)
        else:
            minor_issues.append(issue)

    has_critical = len(critical_issues) > 0

    base_score = 5
    dim_values = list(dimensions.values())

    positive_dims = ["adequada", "ampla", "consistente", "presente"]
    bonus = sum(1 for v in dim_values if v in positive_dims)

    penalty = (len(critical_issues) * 2) + len(minor_issues)
    penalty = min(penalty, 6)

    strength_bonus = min(len(strengths), 3)

    score = max(0, min(10, base_score + bonus + strength_bonus - penalty))

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
    """Gera justificativa contextualizada com detalhes por dimensão."""
    parts = []

    parts.append(
        f"Avaliação baseada em {len(strengths)} pontos fortes e {len(issues)} problemas "
        f"({len(critical_issues)} críticos, {len(minor_issues)} menores)."
    )

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

    if strengths and strengths[0] != "Documentação existente.":
        parts.append(f"Destaque positivo: {strengths[0].rstrip('.')}")

    if issues:
        main_issue = issues[0].get("observation", "")
        if main_issue:
            parts.append(f"Principal ponto de atenção: {main_issue.rstrip('.')}")

    if has_critical:
        parts.append(
            f"A nota foi limitada a no máximo {MAX_SCORE_WITH_CRITICAL} devido a problemas críticos pendentes."
        )

    return ". ".join(parts) + "."
