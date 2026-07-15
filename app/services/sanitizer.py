"""Serviço de sanitização de credenciais na saída do agente."""

import re


# Padrões de variáveis sensíveis (case-insensitive)
SENSITIVE_PATTERNS = [
    r"(?i)\b[\w]*KEY[\w]*\s*[=:]\s*\S+",
    r"(?i)\b[\w]*SECRET[\w]*\s*[=:]\s*\S+",
    r"(?i)\b[\w]*TOKEN[\w]*\s*[=:]\s*\S+",
    r"(?i)\b[\w]*PASSWORD[\w]*\s*[=:]\s*\S+",
    r"(?i)\b[\w]*PASSWD[\w]*\s*[=:]\s*\S+",
    r"(?i)\b[\w]*API_KEY[\w]*\s*[=:]\s*\S+",
]

# Padrão para valores inline que parecem tokens/keys (hex, base64 longos)
INLINE_SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|token|secret|password|passwd)\s*[=:]\s*['\"]?([^\s'\"]{8,})['\"]?",
]

REDACTED = "[REDACTED]"


def sanitize_text(text: str) -> str:
    """Remove credenciais e valores sensíveis de um texto.

    Detecta padrões KEY=valor, SECRET=valor, TOKEN=valor, PASSWORD=valor
    e substitui o valor por [REDACTED].

    Args:
        text: Texto a ser sanitizado.

    Returns:
        Texto com credenciais substituídas por [REDACTED].
    """
    if not text:
        return text

    result = text

    # Substituir valores de variáveis sensíveis (formato VAR=valor ou VAR: valor)
    for pattern in SENSITIVE_PATTERNS:
        result = re.sub(
            pattern,
            lambda m: _redact_value(m.group(0)),
            result,
        )

    return result


def _redact_value(match_text: str) -> str:
    """Substitui apenas o valor (após = ou :) por [REDACTED]."""
    # Encontrar o separador (= ou :)
    for sep in ("=", ":"):
        if sep in match_text:
            parts = match_text.split(sep, 1)
            return f"{parts[0]}{sep} {REDACTED}"
    return match_text


def sanitize_state(state: dict) -> dict:
    """Sanitiza todos os campos de texto do estado do agente.

    Aplica sanitize_text em campos string e em mensagens de erro.
    Não altera o estado original (retorna cópia).

    Args:
        state: Estado do agente.

    Returns:
        Cópia do estado com credenciais removidas.
    """
    sanitized = dict(state)

    # Sanitizar campos string
    string_fields = [
        "raw_input", "validation_message", "readme_content",
        "prd_content", "merged_context", "final_report",
    ]

    for field in string_fields:
        value = sanitized.get(field)
        if isinstance(value, str):
            sanitized[field] = sanitize_text(value)

    # Sanitizar erros
    errors = sanitized.get("errors", [])
    if errors:
        sanitized_errors = []
        for error in errors:
            sanitized_error = dict(error)
            if "message" in sanitized_error:
                sanitized_error["message"] = sanitize_text(sanitized_error["message"])
            sanitized_errors.append(sanitized_error)
        sanitized["errors"] = sanitized_errors

    return sanitized
