"""Nó read_readme: lê e normaliza arquivos README (executa em paralelo)."""

from pathlib import Path

from app.agent.state import AgentState
from app.tools.file_tools import read_markdown_file
from app.tools.text_tools import normalize_document_text


def read_readme(state: AgentState) -> dict:
    """Lê arquivos README dentre os descobertos.

    Faz parte do fan-out paralelo: este nó processa apenas arquivos
    cujo nome contém 'readme'. Executa em paralelo com read_prd_docs.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com readme_content e erros.
    """
    discovered_files = state.get("discovered_files", [])
    errors: list[dict] = []

    readme_content: str | None = None

    for file_path in discovered_files:
        filename_lower = Path(file_path).name.lower()

        if "readme" not in filename_lower:
            continue

        content, error = read_markdown_file(file_path)

        if error:
            errors.append({"node": "read_readme", "message": f"{file_path}: {error}"})
            continue

        if content is None:
            continue

        normalized = normalize_document_text(content)

        if normalized and readme_content is None:
            readme_content = normalized

    return {
        "readme_content": readme_content,
        "errors": errors,
    }
