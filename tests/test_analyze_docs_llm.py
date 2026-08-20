"""Testes para integração LLM no nó analyze_docs.

Testa:
- Chamada LLM com sucesso e parsing correto
- Fallback para heurística quando LLM falha
- Fallback quando variáveis de ambiente ausentes
- Validação e normalização do resultado LLM
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agent.nodes.analyze_docs import (
    analyze_docs,
    _try_llm_analysis,
    _parse_llm_response,
    _validate_and_normalize,
)


# --- Fixtures ---


@pytest.fixture
def state_with_context():
    """Estado com merged_context suficiente para análise."""
    return {
        "raw_input": "https://github.com/example/repo",
        "input_type": "url",
        "validation_status": "valid",
        "validation_message": "",
        "repository_url": "https://github.com/example/repo",
        "local_files": [],
        "discovered_files": ["README.md"],
        "readme_content": "# Projeto\n\nDescrição do projeto.\n\n## Instalação\n\npip install projeto",
        "prd_content": None,
        "merged_context": (
            "# Projeto Exemplo\n\n"
            "Descrição completa do projeto com conteúdo suficiente para análise.\n\n"
            "## Instalação\n\npip install projeto\n\n"
            "## Uso\n\n```python\nimport projeto\nprojeto.run()\n```\n\n"
            "## Contribuição\n\nEnvie um pull request.\n\n"
            "## Licença\n\nMIT License.\n"
        ),
        "analysis_result": None,
        "final_report": None,
        "errors": [],
    }


@pytest.fixture
def valid_llm_response():
    """Resposta JSON válida simulando retorno do LLM."""
    return {
        "dimensions": {
            "clareza": "adequada",
            "cobertura": "ampla",
            "consistencia": "consistente",
            "onboarding": "presente",
        },
        "strengths": [
            "Estrutura clara com seções bem organizadas.",
            "Instruções de instalação presentes e funcionais.",
            "Exemplos de código incluídos.",
        ],
        "issues": [
            {
                "observation": "Ausência de seção de testes.",
                "recommendation": "Adicionar instruções de como executar os testes.",
            }
        ],
        "score": 8,
        "justification": "Documentação bem estruturada e completa. Falta apenas seção de testes para nota máxima.",
        "base_insuficiente": False,
    }


# --- Testes de integração LLM com sucesso ---


class TestLLMIntegration:
    """Testes para chamada LLM com sucesso."""

    @patch("app.agent.nodes.analyze_docs.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "LLM_MODEL": "gpt-4o-mini"})
    def test_analyze_docs_uses_llm_when_available(
        self, mock_openai_class, state_with_context, valid_llm_response
    ):
        """Verifica que analyze_docs usa LLM quando API key e modelo estão configurados."""
        # Configurar mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(valid_llm_response)
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze_docs(state_with_context)

        assert result["analysis_result"] is not None
        assert result["analysis_result"]["score"] == 8
        assert result["analysis_result"]["dimensions"]["clareza"] == "adequada"
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.agent.nodes.analyze_docs.OpenAI")
    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-key",
        "LLM_MODEL": "grok-3",
        "OPENAI_BASE_URL": "https://api.x.ai/v1",
    })
    def test_analyze_docs_uses_custom_base_url(
        self, mock_openai_class, state_with_context, valid_llm_response
    ):
        """Verifica que OPENAI_BASE_URL é passado ao cliente."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(valid_llm_response)
        mock_client.chat.completions.create.return_value = mock_response

        analyze_docs(state_with_context)

        # Verificar que OpenAI foi chamado com base_url
        mock_openai_class.assert_called_once()
        call_kwargs = mock_openai_class.call_args[1]
        assert call_kwargs["base_url"] == "https://api.x.ai/v1"


# --- Testes de fallback ---


class TestFallbackHeuristic:
    """Testes para fallback quando LLM indisponível."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "", "LLM_MODEL": ""}, clear=False)
    def test_fallback_when_no_api_key(self, state_with_context):
        """Sem API key, deve usar análise heurística."""
        result = analyze_docs(state_with_context)

        assert result["analysis_result"] is not None
        assert "dimensions" in result["analysis_result"]
        assert "score" in result["analysis_result"]

    @patch("app.agent.nodes.analyze_docs.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "LLM_MODEL": "gpt-4o-mini"})
    def test_fallback_when_api_timeout(self, mock_openai_class, state_with_context):
        """Timeout da API deve acionar fallback heurístico."""
        from openai import APITimeoutError

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())

        result = analyze_docs(state_with_context)

        assert result["analysis_result"] is not None
        # Fallback heurístico sempre gera resultado válido
        assert "dimensions" in result["analysis_result"]

    @patch("app.agent.nodes.analyze_docs.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "LLM_MODEL": "gpt-4o-mini"})
    def test_fallback_when_rate_limited(self, mock_openai_class, state_with_context):
        """Rate limit deve acionar fallback heurístico."""
        from openai import RateLimitError

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="rate limited",
            response=mock_response,
            body=None,
        )

        result = analyze_docs(state_with_context)

        assert result["analysis_result"] is not None
        assert "dimensions" in result["analysis_result"]

    @patch("app.agent.nodes.analyze_docs.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "LLM_MODEL": "gpt-4o-mini"})
    def test_fallback_when_invalid_json_response(self, mock_openai_class, state_with_context):
        """Resposta não-JSON do LLM deve acionar fallback."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Isto não é JSON válido"
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze_docs(state_with_context)

        assert result["analysis_result"] is not None
        assert "dimensions" in result["analysis_result"]


# --- Testes de parsing ---


class TestParseResponse:
    """Testes para _parse_llm_response."""

    def test_parse_valid_json(self, valid_llm_response):
        """JSON válido com todos os campos deve retornar dict."""
        raw = json.dumps(valid_llm_response)
        result = _parse_llm_response(raw)

        assert result is not None
        assert result["score"] == 8
        assert len(result["strengths"]) == 3

    def test_parse_invalid_json(self):
        """JSON inválido retorna None."""
        result = _parse_llm_response("not json at all")
        assert result is None

    def test_parse_missing_fields(self):
        """JSON com campos faltando retorna None."""
        incomplete = json.dumps({"score": 5, "dimensions": {}})
        result = _parse_llm_response(incomplete)
        assert result is None

    def test_parse_wrong_types(self):
        """JSON com tipos errados retorna None."""
        wrong_types = json.dumps({
            "dimensions": "should be dict",
            "strengths": "should be list",
            "issues": "should be list",
            "score": "should be int",
            "justification": 123,
        })
        result = _parse_llm_response(wrong_types)
        assert result is None


# --- Testes de validação/normalização ---


class TestValidateAndNormalize:
    """Testes para _validate_and_normalize."""

    def test_score_capped_at_10(self, valid_llm_response):
        """Score > 10 deve ser limitado a 10."""
        valid_llm_response["score"] = 15
        result = _validate_and_normalize(valid_llm_response, "x" * 200)
        assert result["score"] == 10

    def test_score_min_zero(self, valid_llm_response):
        """Score < 0 deve ser limitado a 0."""
        valid_llm_response["score"] = -5
        result = _validate_and_normalize(valid_llm_response, "x" * 200)
        assert result["score"] == 0

    def test_score_capped_for_insufficient_base(self, valid_llm_response):
        """Score deve ser limitado a 3 quando base insuficiente."""
        valid_llm_response["score"] = 8
        result = _validate_and_normalize(valid_llm_response, "short")
        assert result["score"] <= 3
        assert result["base_insuficiente"] is True

    def test_strengths_limited_to_10(self, valid_llm_response):
        """Strengths limitados a 10 itens."""
        valid_llm_response["strengths"] = [f"Ponto {i}" for i in range(20)]
        result = _validate_and_normalize(valid_llm_response, "x" * 200)
        assert len(result["strengths"]) == 10

    def test_issues_limited_to_15(self, valid_llm_response):
        """Issues limitados a 15 itens."""
        valid_llm_response["issues"] = [
            {"observation": f"Issue {i}", "recommendation": f"Fix {i}"}
            for i in range(20)
        ]
        result = _validate_and_normalize(valid_llm_response, "x" * 200)
        assert len(result["issues"]) == 15

    def test_empty_strengths_gets_default(self, valid_llm_response):
        """Lista vazia de strengths recebe valor padrão."""
        valid_llm_response["strengths"] = []
        result = _validate_and_normalize(valid_llm_response, "x" * 200)
        assert len(result["strengths"]) >= 1

    def test_empty_issues_gets_default(self, valid_llm_response):
        """Lista vazia de issues recebe valor padrão."""
        valid_llm_response["issues"] = []
        result = _validate_and_normalize(valid_llm_response, "x" * 200)
        assert len(result["issues"]) >= 1
