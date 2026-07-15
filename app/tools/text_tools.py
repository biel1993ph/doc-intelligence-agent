"""Ferramentas de normalização de texto para documentação."""

import re


def normalize_document_text(text: str) -> str:
    """Normaliza texto de documento Markdown.

    Operações:
    - Remove linhas em branco consecutivas (mantém no máximo uma)
    - Aplica trim em cada linha
    - Garante encoding UTF-8 (string Python já é Unicode)
    - Remove espaços em branco no início e fim do documento

    A função é idempotente: aplicá-la múltiplas vezes produz o mesmo resultado.

    Args:
        text: Texto bruto do documento.

    Returns:
        Texto normalizado.
    """
    if not text:
        return ""

    # Trim em cada linha
    lines = [line.strip() for line in text.splitlines()]

    # Remover linhas em branco consecutivas (manter no máximo 1)
    normalized_lines: list[str] = []
    prev_blank = False

    for line in lines:
        if line == "":
            if not prev_blank:
                normalized_lines.append(line)
            prev_blank = True
        else:
            normalized_lines.append(line)
            prev_blank = False

    # Trim do documento inteiro
    result = "\n".join(normalized_lines).strip()

    return result
