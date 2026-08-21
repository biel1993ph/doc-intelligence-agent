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


import logging
import os
import re
from typing import TypedDict

logger = logging.getLogger(__name__)


class RepositoryMetadata(TypedDict):
    """Schema de saída dos metadados do repositório GitHub."""

    owner: str
    repo: str
    full_name: str
    description: str | None
    language: str | None
    stars: int
    forks: int
    open_issues: int
    default_branch: str
    created_at: str
    updated_at: str
    pushed_at: str
    topics: list[str]


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extrai owner e repo de uma URL do GitHub.

    Aceita formatos:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch

    Args:
        url: URL do repositório.

    Returns:
        Tupla (owner, repo) ou None se não for URL do GitHub.
    """
    pattern = r"github\.com[/:]([^/]+)/([^/.]+)"
    match = re.search(pattern, url)
    if not match:
        return None
    owner = match.group(1)
    repo = match.group(2).removesuffix(".git")
    return owner, repo


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout)),
    reraise=True,
)
def _github_api_request(api_url: str, headers: dict) -> requests.Response:
    """Faz requisição GET à GitHub API com retry limitado."""
    return requests.get(api_url, headers=headers, timeout=15)


def fetch_repository_metadata(url: str) -> tuple[RepositoryMetadata | None, str | None]:
    """Busca metadados de um repositório via GitHub REST API.

    Integração via API externa com:
    - Validação de entrada (owner/repo extraídos da URL)
    - Schema de saída definido (RepositoryMetadata)
    - Tratamento de erros (404, 403, timeout, conexão)
    - Retry com backoff exponencial (max 2 retentativas)
    - Token GitHub opcional para rate limit

    Args:
        url: URL do repositório GitHub.

    Returns:
        Tupla (metadata, error). Em sucesso, error é None.
        Se a URL não for do GitHub, retorna (None, None) — não é erro.
    """
    # Validar entrada: extrair owner/repo
    parsed = parse_github_url(url)
    if parsed is None:
        # Não é URL do GitHub — pular gracefully
        return None, None

    owner, repo = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Headers com token opcional
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "doc-intelligence-agent",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = _github_api_request(api_url, headers)
    except requests.exceptions.Timeout:
        logger.warning("GitHub API timeout para %s/%s", owner, repo)
        return None, f"GitHub API timeout para {owner}/{repo}"
    except requests.exceptions.ConnectionError:
        logger.warning("GitHub API erro de conexão para %s/%s", owner, repo)
        return None, f"GitHub API erro de conexão para {owner}/{repo} (após retry)"
    except requests.exceptions.RequestException as e:
        logger.warning("GitHub API erro: %s", e)
        return None, f"GitHub API erro: {e}"

    # Tratamento de status HTTP
    if response.status_code == 404:
        return None, f"Repositório não encontrado: {owner}/{repo}"
    if response.status_code == 403:
        return None, f"GitHub API rate limit atingido para {owner}/{repo}"
    if response.status_code >= 400:
        return None, f"GitHub API erro HTTP {response.status_code} para {owner}/{repo}"

    # Parsear resposta
    try:
        data = response.json()
    except ValueError:
        return None, "GitHub API resposta inválida (não JSON)"

    # Montar schema de saída validado
    metadata: RepositoryMetadata = {
        "owner": data.get("owner", {}).get("login", owner),
        "repo": data.get("name", repo),
        "full_name": data.get("full_name", f"{owner}/{repo}"),
        "description": data.get("description"),
        "language": data.get("language"),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "default_branch": data.get("default_branch", "main"),
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "pushed_at": data.get("pushed_at", ""),
        "topics": data.get("topics", []),
    }

    logger.info("Metadados obtidos para %s/%s: %d stars, %d forks", owner, repo, metadata["stars"], metadata["forks"])
    return metadata, None
