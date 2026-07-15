"""Configuração compartilhada de testes: perfis Hypothesis, fixtures e generators."""

import os
import tempfile
from pathlib import Path

import pytest
from hypothesis import settings, HealthCheck

from app.agent.state import AgentState


# --- Perfis Hypothesis ---

settings.register_profile(
    "dev",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    "ci",
    max_examples=200,
    suppress_health_check=[HealthCheck.too_slow],
)

# Usar perfil baseado na variável de ambiente
profile = os.environ.get("HYPOTHESIS_PROFILE", "dev")
settings.load_profile(profile)


# --- Fixtures ---


@pytest.fixture
def empty_state() -> AgentState:
    """Estado inicial vazio do agente."""
    return {
        "raw_input": "",
        "input_type": "",
        "validation_status": "",
        "validation_message": "",
        "repository_url": None,
        "local_files": [],
        "discovered_files": [],
        "readme_content": None,
        "prd_content": None,
        "merged_context": None,
        "analysis_result": None,
        "final_report": None,
        "errors": [],
    }


@pytest.fixture
def valid_url_state() -> AgentState:
    """Estado com URL válida pré-preenchida."""
    return {
        "raw_input": "https://github.com/example/repo",
        "input_type": "url",
        "validation_status": "valid",
        "validation_message": "URL válida e acessível.",
        "repository_url": "https://github.com/example/repo",
        "local_files": [],
        "discovered_files": [],
        "readme_content": None,
        "prd_content": None,
        "merged_context": None,
        "analysis_result": None,
        "final_report": None,
        "errors": [],
    }


@pytest.fixture
def local_dir_with_readme(tmp_path: Path) -> Path:
    """Diretório temporário com README.md."""
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Projeto Exemplo\n\n"
        "Descrição do projeto com conteúdo suficiente para análise.\n\n"
        "## Instalação\n\npip install projeto\n\n"
        "## Uso\n\nExemplo de uso detalhado aqui.\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def local_dir_with_readme_and_prd(tmp_path: Path) -> Path:
    """Diretório temporário com README.md e PRD.md."""
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Projeto\n\nDescrição completa do projeto.\n\n"
        "## Instalação\n\npip install projeto\n\n"
        "## Uso\n\nExemplo detalhado.\n",
        encoding="utf-8",
    )
    prd = tmp_path / "PRD.md"
    prd.write_text(
        "# Product Requirements\n\n"
        "## Visão Geral\n\nProduto para resolver X.\n\n"
        "## Funcionalidades\n\n- Feature A\n- Feature B\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def sample_analysis_result() -> dict:
    """Resultado de análise pré-populado."""
    return {
        "dimensions": {
            "clareza": "adequada",
            "cobertura": "parcial",
            "consistencia": "consistente",
            "onboarding": "presente",
        },
        "strengths": [
            "Estrutura com cabeçalhos Markdown presente.",
            "Instruções de instalação disponíveis.",
        ],
        "issues": [
            {
                "observation": "Ausência de exemplos de código.",
                "recommendation": "Adicionar blocos de código com exemplos.",
            }
        ],
        "score": 7,
        "justification": "Boa documentação com estrutura clara. Pode melhorar em exemplos práticos.",
        "base_insuficiente": False,
    }
