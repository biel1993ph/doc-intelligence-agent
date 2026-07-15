"""Nó validate_input: valida a entrada do usuário."""

from pathlib import Path

from app.agent.state import AgentState
from app.tools.repo_tools import validate_repository_url
from app.tools.file_tools import VALID_EXTENSIONS


def validate_input(state: AgentState) -> dict:
    """Valida a entrada com base no input_type identificado.

    Regras de validação:
    - empty → invalid
    - url → valida via validate_repository_url
    - path → verifica existência e extensões .md/.markdown

    Retorna apenas os campos que este nó é responsável por atualizar:
    validation_status, validation_message, repository_url, local_files.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com campos de validação.
    """
    input_type = state.get("input_type", "empty")
    raw_input = state.get("raw_input", "")

    # Entrada vazia
    if input_type == "empty" or not raw_input:
        return {
            "validation_status": "invalid",
            "validation_message": "Entrada vazia: forneça uma URL de repositório ou caminho local.",
            "repository_url": None,
            "local_files": [],
        }

    # Validação de URL
    if input_type == "url":
        valid, message = validate_repository_url(raw_input)
        if valid:
            return {
                "validation_status": "valid",
                "validation_message": message,
                "repository_url": raw_input,
                "local_files": [],
            }
        else:
            return {
                "validation_status": "invalid",
                "validation_message": message,
                "repository_url": None,
                "local_files": [],
            }

    # Validação de caminho local
    if input_type == "path":
        path = Path(raw_input)

        if not path.exists():
            return {
                "validation_status": "invalid",
                "validation_message": f"Caminho não encontrado: {raw_input}",
                "repository_url": None,
                "local_files": [],
            }

        # Se é diretório, aceitar
        if path.is_dir():
            return {
                "validation_status": "valid",
                "validation_message": "Diretório local válido.",
                "repository_url": None,
                "local_files": [str(path.resolve())],
            }

        # Se é arquivo, verificar extensão
        if path.is_file():
            if path.suffix.lower() in VALID_EXTENSIONS:
                return {
                    "validation_status": "valid",
                    "validation_message": "Arquivo Markdown válido.",
                    "repository_url": None,
                    "local_files": [str(path.resolve())],
                }
            else:
                return {
                    "validation_status": "invalid",
                    "validation_message": f"Extensão inválida: {path.suffix}. Aceitas: .md, .markdown",
                    "repository_url": None,
                    "local_files": [],
                }

    # Tipo desconhecido
    return {
        "validation_status": "invalid",
        "validation_message": f"Tipo de entrada não reconhecido: {input_type}",
        "repository_url": None,
        "local_files": [],
    }
