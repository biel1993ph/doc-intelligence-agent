"""Ferramentas de validação de URL e clonagem de repositório."""

import tempfile
import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests
from git import Repo, GitCommandError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


def validate_repository_url(url: str) -> tuple[bool, str]:
    """Valida URL de repositório sintaticamente e por acessibilidade.

    Verifica:
    - Esquema http ou https
    - Host válido (não vazio)
    - Acessibilidade com timeout de 30 segundos

    Args:
        url: URL do repositório a validar.

    Returns:
        Tupla (valido, mensagem) indicando resultado da validação.
    """
    # Validação sintática
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL malformada: não foi possível fazer parsing."

    if parsed.scheme not in ("http", "https"):
        return False, f"Esquema inválido: '{parsed.scheme}'. Apenas http/https são aceitos."

    if not parsed.hostname:
        return False, "Host inválido: URL não contém hostname."

    # Validação de acessibilidade
    try:
        response = _request_with_retry(url)
        if response.status_code >= 400:
            return False, f"URL inacessível: status HTTP {response.status_code}."
    except requests.exceptions.Timeout:
        return False, "URL inacessível: timeout de 30 segundos excedido."
    except requests.exceptions.ConnectionError:
        return False, "URL inacessível: erro de conexão (após retry)."
    except requests.exceptions.RequestException as e:
        return False, f"URL inacessível: {e}"

    return True, "URL válida e acessível."


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout)),
    reraise=True,
)
def _request_with_retry(url: str) -> requests.Response:
    """Faz requisição HEAD com retry limitado (max 2 retentativas)."""
    return requests.head(url, timeout=30, allow_redirects=True)


def clone_or_open_repository(url: str) -> tuple[str, str | None]:
    """Clona repositório remoto ou abre diretório local.

    Realiza validação da URL antes de clonar. Usa tempfile.TemporaryDirectory
    para armazenamento temporário e limpa em caso de falha.

    Args:
        url: URL do repositório remoto ou caminho de diretório local.

    Returns:
        Tupla (caminho_do_repositorio, mensagem_de_erro).
        Em caso de sucesso, mensagem_de_erro é None.
        Em caso de falha, caminho é string vazia e mensagem_de_erro descreve o problema.
    """
    # Verificar se é diretório local
    local_path = Path(url)
    if local_path.exists() and local_path.is_dir():
        return str(local_path.resolve()), None

    # Validar URL antes de clonar
    valid, message = validate_repository_url(url)
    if not valid:
        return "", f"Validação falhou: {message}"

    # Clonar repositório
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="doc_intel_")
        Repo.clone_from(
            url,
            tmp_dir,
            multi_options=["--depth=1"],
            kill_after_timeout=60,
        )
        return tmp_dir, None
    except GitCommandError as e:
        # Limpar diretório temporário em caso de falha
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return "", f"Falha na clonagem: {e}"
    except Exception as e:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return "", f"Erro inesperado: {e}"
