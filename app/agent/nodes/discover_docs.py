"""Nó discover_docs: localiza arquivos de documentação no repositório/diretório."""

from pathlib import Path

from app.agent.state import AgentState
from app.tools.repo_tools import clone_or_open_repository, fetch_repository_metadata
from app.tools.file_tools import find_documentation_files, VALID_EXTENSIONS


def discover_docs(state: AgentState) -> dict:
    """Descobre arquivos de documentação a partir do repositório ou caminho local.

    Para URLs: clona o repositório e busca documentos.
    Para caminhos locais: verifica existência e busca documentos.

    Se nenhum documento for encontrado, registra erro e sinaliza fim.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com discovered_files e possíveis erros.
    """
    repository_url = state.get("repository_url")
    local_files = state.get("local_files", [])
    errors: list[dict] = []

    # Determinar diretório raiz para busca
    root_path: str | None = None
    repository_metadata = None

    if repository_url:
        # Clonar repositório remoto
        path, error = clone_or_open_repository(repository_url)
        if error:
            errors.append({"node": "discover_docs", "message": error})
            return {
                "discovered_files": [],
                "errors": errors,
            }
        root_path = path

        # Buscar metadados via GitHub API (se for URL do GitHub)
        metadata, meta_error = fetch_repository_metadata(repository_url)
        if meta_error:
            errors.append({"node": "discover_docs", "message": f"Metadados: {meta_error}"})
        repository_metadata = metadata

    elif local_files:
        # Usar caminho local
        local = Path(local_files[0])
        if local.is_dir():
            root_path = str(local)
        elif local.is_file():
            # Se é arquivo individual, verificar extensão e retornar diretamente
            if local.suffix.lower() in VALID_EXTENSIONS:
                return {
                    "discovered_files": [str(local.resolve())],
                    "errors": errors,
                }
            else:
                errors.append({
                    "node": "discover_docs",
                    "message": f"Arquivo com extensão inválida: {local.suffix}",
                })
                return {
                    "discovered_files": [],
                    "errors": errors,
                }
        else:
            errors.append({
                "node": "discover_docs",
                "message": f"Caminho local não encontrado: {local_files[0]}",
            })
            return {
                "discovered_files": [],
                "errors": errors,
            }
    else:
        errors.append({
            "node": "discover_docs",
            "message": "Nenhuma fonte de dados disponível (URL ou caminho local).",
        })
        return {
            "discovered_files": [],
            "errors": errors,
        }

    # Buscar documentos no diretório
    relative_files = find_documentation_files(root_path)

    if not relative_files:
        errors.append({
            "node": "discover_docs",
            "message": "Nenhum documento de documentação encontrado no repositório.",
        })
        return {
            "discovered_files": [],
            "errors": errors,
        }

    # Converter para caminhos absolutos
    root = Path(root_path)
    absolute_files = [str((root / f).resolve()) for f in relative_files]

    result = {
        "discovered_files": absolute_files,
        "errors": errors,
        "repository_metadata": repository_metadata,
    }

    return result
