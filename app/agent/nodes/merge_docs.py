"""Nó merge_docs: consolida resultados dos nós paralelos de leitura (fan-in)."""

from pathlib import Path

from app.agent.state import AgentState
from app.tools.file_tools import read_markdown_file
from app.tools.text_tools import normalize_document_text


MAX_FILES_PER_EXECUTION = 20


def merge_docs(state: AgentState) -> dict:
    """Consolida readme_content e prd_content em merged_context.

    Este nó atua como fan-in/join após a execução paralela de
    read_readme e read_prd_docs. Lê todos os arquivos descobertos
    e monta o merged_context com cabeçalhos de rastreabilidade.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com merged_context e erros.
    """
    discovered_files = state.get("discovered_files", [])
    errors: list[dict] = []
    merged_parts: list[str] = []

    files_to_read = discovered_files[:MAX_FILES_PER_EXECUTION]

    for file_path in files_to_read:
        content, error = read_markdown_file(file_path)

        if error:
            errors.append({"node": "merge_docs", "message": f"{file_path}: {error}"})
            continue

        if content is None:
            continue

        normalized = normalize_document_text(content)

        if not normalized:
            continue

        header = f"--- Fonte: {Path(file_path).name} ---"
        merged_parts.append(f"{header}\n\n{normalized}")

    merged_context = "\n\n".join(merged_parts) if merged_parts else None

    if not merged_context:
        errors.append({
            "node": "merge_docs",
            "message": "Nenhum conteúdo válido lido dos documentos descobertos.",
        })

    return {
        "merged_context": merged_context,
        "errors": errors,
    }
