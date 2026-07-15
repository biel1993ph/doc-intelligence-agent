"""Testes de propriedade para sanitização de credenciais."""

from hypothesis import given, strategies as st, settings

from app.services.sanitizer import sanitize_text, sanitize_state, REDACTED


# Estratégias para gerar nomes de variáveis sensíveis
sensitive_prefixes = st.sampled_from(["API_KEY", "SECRET", "TOKEN", "PASSWORD", "AWS_SECRET_KEY", "DB_PASSWORD", "AUTH_TOKEN", "PRIVATE_KEY"])
separators = st.sampled_from(["=", ": ", "="])
secret_values = st.from_regex(r"[A-Za-z0-9+/]{8,40}", fullmatch=True)


@given(
    prefix=sensitive_prefixes,
    sep=separators,
    value=secret_values,
)
@settings(max_examples=100)
def test_credentials_never_exposed(prefix: str, sep: str, value: str) -> None:
    """Credenciais com padrão KEY/SECRET/TOKEN/PASSWORD são sempre redacted."""
    text = f"Config: {prefix}{sep}{value} e mais texto"
    result = sanitize_text(text)

    assert value not in result, f"Valor '{value}' encontrado na saída sanitizada"
    assert REDACTED in result


@given(
    prefix=sensitive_prefixes,
    sep=separators,
    value=secret_values,
)
@settings(max_examples=50)
def test_sanitize_state_removes_credentials_from_final_report(prefix: str, sep: str, value: str) -> None:
    """Credenciais não aparecem em final_report após sanitização."""
    report = f"# Relatório\n\n{prefix}{sep}{value}\n\nFim do relatório."
    state = {
        "raw_input": "",
        "input_type": "",
        "validation_status": "valid",
        "validation_message": "",
        "repository_url": None,
        "local_files": [],
        "discovered_files": [],
        "readme_content": None,
        "prd_content": None,
        "merged_context": None,
        "analysis_result": None,
        "final_report": report,
        "errors": [],
    }

    sanitized = sanitize_state(state)
    assert value not in sanitized["final_report"]


@given(
    prefix=sensitive_prefixes,
    sep=separators,
    value=secret_values,
)
@settings(max_examples=50)
def test_sanitize_state_removes_credentials_from_errors(prefix: str, sep: str, value: str) -> None:
    """Credenciais não aparecem em mensagens de erro após sanitização."""
    state = {
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
        "errors": [{"node": "test", "message": f"Erro: {prefix}{sep}{value}"}],
    }

    sanitized = sanitize_state(state)
    for error in sanitized["errors"]:
        assert value not in error["message"]


def test_sanitize_text_preserves_normal_text() -> None:
    """Texto sem credenciais não é alterado."""
    text = "Este é um relatório normal sem nenhuma credencial visível."
    result = sanitize_text(text)
    assert result == text


def test_sanitize_text_empty() -> None:
    """Texto vazio retorna vazio."""
    assert sanitize_text("") == ""
    assert sanitize_text(None) is None


def test_sanitize_multiple_credentials() -> None:
    """Múltiplas credenciais no mesmo texto são todas removidas."""
    text = "API_KEY=abc123secret TOKEN=xyz789token PASSWORD=mypassword123"
    result = sanitize_text(text)

    assert "abc123secret" not in result
    assert "xyz789token" not in result
    assert "mypassword123" not in result
    assert result.count(REDACTED) == 3


def test_sanitize_state_does_not_modify_original() -> None:
    """sanitize_state não altera o estado original."""
    original_report = "SECRET_KEY=mysecretvalue"
    state = {
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
        "final_report": original_report,
        "errors": [],
    }

    sanitize_state(state)
    assert state["final_report"] == original_report
