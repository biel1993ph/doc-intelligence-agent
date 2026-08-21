"""Sanitização e detecção de prompt injection em conteúdo de documentos.

Protege o agente contra tentativas de manipulação via conteúdo
malicioso em documentos analisados (README, PRD, etc.).

Estratégia de defesa em profundidade:
1. Detecção de padrões maliciosos conhecidos
2. Envolvimento com delimitadores de segurança
3. Validação pós-LLM da resposta
"""

import logging
import re

logger = logging.getLogger(__name__)

# Padrões de prompt injection conhecidos (case-insensitive)
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts)",
    r"ignore\s+todas\s+as\s+instru[çc][õo]es",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+a",
    r"voc[êe]\s+agora\s+[ée]\s+um",
    r"reveal\s+(your\s+)?(system\s+prompt|api\s*key|secret|instructions)",
    r"exib[ai]\s+(sua\s+)?(api\s*key|chave|prompt|instru[çc][õo]es)",
    r"print\s+(your\s+)?(system|api|secret|prompt)",
    r"override\s+(scoring|rules|instructions|system)",
    r"set\s+score\s+to\s+\d+",
    r"defina\s+(a\s+)?nota\s+(como|para)\s+\d+",
    r"INJECTION_SUCCESS",
    r"SYSTEM:\s*Override",
    r"</?(system|assistant|user)>",
    r"\[INST\]|\[/INST\]",
    r"<<SYS>>|<</SYS>>",
]

# Compilar padrões para performance
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

# Delimitadores de segurança
UNTRUSTED_START = "--- INÍCIO DO CONTEÚDO NÃO CONFIÁVEL (DOCUMENTO ANALISADO) ---"
UNTRUSTED_END = "--- FIM DO CONTEÚDO NÃO CONFIÁVEL ---"


def detect_injection_attempts(content: str) -> list[str]:
    """Detecta tentativas de prompt injection no conteúdo.

    Args:
        content: Texto do documento a ser analisado.

    Returns:
        Lista de padrões detectados (vazia se nenhum encontrado).
    """
    detections = []
    for pattern in _COMPILED_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            detections.append(pattern.pattern)

    if detections:
        logger.warning(
            "Prompt injection detectado: %d padrões encontrados",
            len(detections),
        )

    return detections


def wrap_with_delimiters(content: str) -> str:
    """Envolve conteúdo não confiável com delimitadores de segurança.

    Os delimitadores sinalizam ao LLM que o conteúdo dentro é
    dados a serem analisados, NÃO instruções a serem seguidas.

    Args:
        content: Conteúdo do documento (não confiável).

    Returns:
        Conteúdo envolvido com delimitadores.
    """
    return f"{UNTRUSTED_START}\n{content}\n{UNTRUSTED_END}"


def sanitize_for_llm(content: str) -> str:
    """Prepara conteúdo para envio ao LLM com proteção contra injection.

    Aplica:
    1. Detecção de padrões (log de warning, mas não bloqueia)
    2. Neutralização de delimitadores internos que possam confundir
    3. Envolvimento com delimitadores de segurança

    A análise não é bloqueada por detecção de injection — o documento
    pode conter exemplos de injection legítimos em contexto educacional.
    O objetivo é que o LLM trate tudo como dados, não instruções.

    Args:
        content: Conteúdo bruto do documento.

    Returns:
        Conteúdo sanitizado e delimitado para envio ao LLM.
    """
    # 1. Detectar (apenas log, não bloqueia)
    detect_injection_attempts(content)

    # 2. Neutralizar delimitadores internos que poderiam encerrar o bloco
    sanitized = content.replace(UNTRUSTED_START, "[DELIMITADOR REMOVIDO]")
    sanitized = sanitized.replace(UNTRUSTED_END, "[DELIMITADOR REMOVIDO]")

    # 3. Envolver com delimitadores
    return wrap_with_delimiters(sanitized)


def validate_llm_response_safety(response: dict) -> tuple[bool, str]:
    """Valida que a resposta do LLM não contém informações do sistema.

    Verifica que o LLM não foi manipulado para revelar:
    - System prompt
    - API keys
    - Variáveis de ambiente
    - Indicadores de injection bem-sucedida

    Args:
        response: Dict com o resultado do LLM já parseado.

    Returns:
        Tupla (seguro, motivo). Se não seguro, motivo descreve o problema.
    """
    # Serializar toda a resposta para inspeção
    response_text = str(response).lower()

    # Padrões que indicam vazamento de informação
    leak_indicators = [
        "injection_success",
        "sk-",  # Prefixo de API key OpenAI
        "xai-",  # Prefixo de API key xAI
        "openai_api_key",
        "system prompt",
        "system_prompt",
        "ignore previous instructions",
        "ignore todas as instruções",
    ]

    for indicator in leak_indicators:
        if indicator in response_text:
            logger.error(
                "Resposta do LLM contém indicador de vazamento: %s",
                indicator,
            )
            return False, f"Indicador de vazamento detectado: {indicator}"

    return True, "Resposta segura"
