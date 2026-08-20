"""Nó read_prd_docs: lê e normaliza arquivos PRD e outros docs (executa em paralelo)."""

from pathlib import Path

from app.agent.state import AgentState
from app.tools.file_tools import read_markdown_file
from app.tools.text_tools import normalize_document_text


MAX_FILES_PER_EXECUTION = 20


def read_prd_docs(state: AgentState) -> dict:
    """Lê arquivos PRD e demais documentos (não-README) dentre os descobertos.

    Faz parte do fan-out paralelo: este nó processa arquivos PRD e
    documentação geral. Executa em paralelo com read_readme.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com prd_content e erros.
    """
    discovered_files = state.get("discovered_files", [])
    errors: list[dict] = []

    prd_content: str | None = None

    # Processar apenas arquivos que não são README
    non_readme_files = [
        f for f in discovered_files
        if "readme" not in Path(f).name.lower()
    ]

    for file_path in non_readme_files[:MAX_FILES_PER_EXECUTION]:
        content, error = read_markdown_file(file_path)

        if error:
            errors.append({"node": "read_prd_docs", "message": f"{file_path}: {error}"})
            continue

        if content is None:
            continue

        normalized = normalize_document_text(content)

        if not normalized:
            continue

        # Identificar PRD
        filename_lower = Path(file_path).name.lower()
        if ("prd" in filename_lower or "product_requirements" in filename_lower) and prd_content is None:
            prd_content = normalized

    return {
        "prd_content": prd_content,
        "errors": errors,
    }
