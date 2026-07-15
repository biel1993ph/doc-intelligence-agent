"""Nó read_docs: lê e normaliza documentos descobertos."""

from pathlib import Path

from app.agent.state import AgentState
from app.tools.file_tools import read_markdown_file
from app.tools.text_tools import normalize_document_text


MAX_FILES_PER_EXECUTION = 20


def read_docs(state: AgentState) -> dict:
    """Lê cada arquivo descoberto, normaliza e consolida em merged_context.

    Identifica README e PRD pelo nome do arquivo.
    Consolida todos os conteúdos em merged_context com cabeçalhos de rastreabilidade.
    Respeita limite de 20 arquivos por execução.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com readme_content, prd_content, merged_context e erros.
    """
    discovered_files = state.get("discovered_files", [])
    errors = list(state.get("errors", []))

    readme_content: str | None = None
    prd_content: str | None = None
    merged_parts: list[str] = []

    # Limitar a 20 arquivos
    files_to_read = discovered_files[:MAX_FILES_PER_EXECUTION]

    for file_path in files_to_read:
        content, error = read_markdown_file(file_path)

        if error:
            errors.append({"node": "read_docs", "message": f"{file_path}: {error}"})
            continue

        if content is None:
            continue

        # Normalizar conteúdo
        normalized = normalize_document_text(content)

        if not normalized:
            continue

        # Identificar tipo de documento pelo nome
        filename_lower = Path(file_path).name.lower()

        if "readme" in filename_lower and readme_content is None:
            readme_content = normalized

        if "prd" in filename_lower or "product_requirements" in filename_lower:
            if prd_content is None:
                prd_content = normalized

        # Adicionar ao contexto consolidado com rastreabilidade
        # Usar caminho relativo se possível, senão o nome do arquivo
        header = f"--- Fonte: {Path(file_path).name} ---"
        merged_parts.append(f"{header}\n\n{normalized}")

    # Consolidar
    merged_context = "\n\n".join(merged_parts) if merged_parts else None

    if not merged_context:
        errors.append({
            "node": "read_docs",
            "message": "Nenhum conteúdo válido lido dos documentos descobertos.",
        })

    return {
        "readme_content": readme_content,
        "prd_content": prd_content,
        "merged_context": merged_context,
        "errors": errors,
    }
