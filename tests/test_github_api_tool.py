"""Testes para a tool fetch_repository_metadata (GitHub API).

Testa:
- Parsing de URL GitHub (vários formatos)
- Chamada à API com mock (200, 404, 403, timeout)
- Retry em caso de erro de conexão
- Schema de saída (campos presentes e tipados)
- Integração no relatório (seção "Informações do Repositório")
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.tools.repo_tools import (
    fetch_repository_metadata,
    parse_github_url,
    RepositoryMetadata,
)
from app.services.report_service import generate_report_markdown


# --- Testes de parsing de URL ---


class TestParseGithubUrl:
    """Testes para extração de owner/repo da URL."""

    def test_standard_url(self):
        """URL padrão https://github.com/owner/repo."""
        result = parse_github_url("https://github.com/biel1993ph/doc-intelligence-agent")
        assert result == ("biel1993ph", "doc-intelligence-agent")

    def test_url_with_git_suffix(self):
        """URL com .git no final."""
        result = parse_github_url("https://github.com/owner/repo.git")
        assert result == ("owner", "repo")

    def test_url_with_tree_branch(self):
        """URL com /tree/branch."""
        result = parse_github_url("https://github.com/owner/repo/tree/main")
        assert result == ("owner", "repo")

    def test_non_github_url(self):
        """URL não-GitHub retorna None."""
        result = parse_github_url("https://gitlab.com/owner/repo")
        assert result is None

    def test_local_path(self):
        """Caminho local retorna None."""
        result = parse_github_url("/home/user/project")
        assert result is None

    def test_empty_string(self):
        """String vazia retorna None."""
        result = parse_github_url("")
        assert result is None


# --- Testes de fetch com mock ---


class TestFetchRepositoryMetadata:
    """Testes para fetch_repository_metadata com mock."""

    @patch("app.tools.repo_tools._github_api_request")
    def test_success_returns_metadata(self, mock_request):
        """API 200 retorna metadata completo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "owner": {"login": "biel1993ph"},
            "name": "doc-intelligence-agent",
            "full_name": "biel1993ph/doc-intelligence-agent",
            "description": "Agente de análise de documentação",
            "language": "Python",
            "stargazers_count": 5,
            "forks_count": 2,
            "open_issues_count": 3,
            "default_branch": "develop",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-06-01T00:00:00Z",
            "pushed_at": "2024-06-01T12:00:00Z",
            "topics": ["langgraph", "agent"],
        }
        mock_request.return_value = mock_response

        metadata, error = fetch_repository_metadata(
            "https://github.com/biel1993ph/doc-intelligence-agent"
        )

        assert error is None
        assert metadata is not None
        assert metadata["owner"] == "biel1993ph"
        assert metadata["repo"] == "doc-intelligence-agent"
        assert metadata["stars"] == 5
        assert metadata["forks"] == 2
        assert metadata["language"] == "Python"
        assert metadata["topics"] == ["langgraph", "agent"]

    @patch("app.tools.repo_tools._github_api_request")
    def test_404_returns_error(self, mock_request):
        """API 404 retorna erro de repositório não encontrado."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        metadata, error = fetch_repository_metadata(
            "https://github.com/nonexistent/repo"
        )

        assert metadata is None
        assert error is not None
        assert "não encontrado" in error

    @patch("app.tools.repo_tools._github_api_request")
    def test_403_returns_rate_limit_error(self, mock_request):
        """API 403 retorna erro de rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_request.return_value = mock_response

        metadata, error = fetch_repository_metadata(
            "https://github.com/owner/repo"
        )

        assert metadata is None
        assert "rate limit" in error

    @patch("app.tools.repo_tools._github_api_request")
    def test_timeout_returns_error(self, mock_request):
        """Timeout retorna erro."""
        mock_request.side_effect = requests.exceptions.Timeout("timeout")

        metadata, error = fetch_repository_metadata(
            "https://github.com/owner/repo"
        )

        assert metadata is None
        assert "timeout" in error.lower()

    @patch("app.tools.repo_tools._github_api_request")
    def test_connection_error_returns_error(self, mock_request):
        """Connection error retorna erro após retry."""
        mock_request.side_effect = requests.exceptions.ConnectionError("failed")

        metadata, error = fetch_repository_metadata(
            "https://github.com/owner/repo"
        )

        assert metadata is None
        assert "conexão" in error.lower()

    def test_non_github_url_returns_none_none(self):
        """URL não-GitHub retorna (None, None) sem erro."""
        metadata, error = fetch_repository_metadata("https://gitlab.com/owner/repo")

        assert metadata is None
        assert error is None

    def test_local_path_returns_none_none(self):
        """Caminho local retorna (None, None) sem erro."""
        metadata, error = fetch_repository_metadata("/tmp/some-dir")

        assert metadata is None
        assert error is None

    @patch("app.tools.repo_tools._github_api_request")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test123"})
    def test_uses_token_when_available(self, mock_request):
        """Usa GITHUB_TOKEN no header quando disponível."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "owner": {"login": "owner"},
            "name": "repo",
            "full_name": "owner/repo",
            "description": None,
            "language": None,
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "default_branch": "main",
            "created_at": "",
            "updated_at": "",
            "pushed_at": "",
            "topics": [],
        }
        mock_request.return_value = mock_response

        fetch_repository_metadata("https://github.com/owner/repo")

        # Verificar que o token foi passado nos headers
        call_args = mock_request.call_args
        headers = call_args[0][1]  # segundo argumento posicional
        assert "Authorization" in headers
        assert "ghp_test123" in headers["Authorization"]


# --- Testes de integração no relatório ---


class TestReportWithMetadata:
    """Testes para seção de metadados no relatório."""

    def test_report_includes_metadata_section(self):
        """Relatório inclui seção 'Informações do Repositório' quando metadata presente."""
        analysis = {
            "dimensions": {"clareza": "adequada"},
            "strengths": ["Boa estrutura"],
            "issues": [],
            "score": 7,
            "justification": "Documentação razoável. Análise completa.",
            "base_insuficiente": False,
        }
        metadata = {
            "full_name": "biel1993ph/doc-intelligence-agent",
            "description": "Agente de documentação",
            "language": "Python",
            "stars": 10,
            "forks": 3,
            "open_issues": 5,
            "default_branch": "develop",
            "pushed_at": "2024-06-01T12:00:00Z",
            "topics": ["langgraph"],
        }

        report = generate_report_markdown(analysis, ["README.md"], metadata)

        assert "Informações do Repositório" in report
        assert "biel1993ph/doc-intelligence-agent" in report
        assert "Python" in report
        assert "10" in report
        assert "langgraph" in report

    def test_report_without_metadata(self):
        """Relatório sem metadados não inclui a seção."""
        analysis = {
            "dimensions": {"clareza": "adequada"},
            "strengths": ["Boa estrutura"],
            "issues": [],
            "score": 7,
            "justification": "Documentação razoável. Análise completa.",
            "base_insuficiente": False,
        }

        report = generate_report_markdown(analysis, ["README.md"], None)

        assert "Informações do Repositório" not in report
