"""Testes de propriedade para nós receive_input e validate_input."""

import tempfile
from pathlib import Path

from hypothesis import given, strategies as st, settings

from app.agent.nodes.receive_input import receive_input
from app.agent.nodes.validate_input import validate_input


def _make_state(**kwargs) -> dict:
    """Cria um estado mínimo para testes."""
    defaults = {
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
    defaults.update(kwargs)
    return defaults


# --- receive_input ---


@given(
    url=st.from_regex(r"https?://[a-z]{1,20}\.[a-z]{2,5}/[a-z0-9]{1,10}", fullmatch=True),
)
@settings(max_examples=50)
def test_receive_input_url_type(url: str) -> None:
    """URLs http/https são classificadas como input_type='url'."""
    state = _make_state(raw_input=url)
    result = receive_input(state)
    assert result["input_type"] == "url"
    assert result["raw_input"] == url


@given(
    path=st.from_regex(r"/[a-z]{1,10}/[a-z]{1,10}\.(md|markdown)", fullmatch=True),
)
@settings(max_examples=50)
def test_receive_input_path_type(path: str) -> None:
    """Caminhos locais são classificados como input_type='path'."""
    state = _make_state(raw_input=path)
    result = receive_input(state)
    assert result["input_type"] == "path"


@given(
    text=st.just(""),
)
def test_receive_input_empty(text: str) -> None:
    """Entrada vazia é classificada como input_type='empty'."""
    state = _make_state(raw_input=text)
    result = receive_input(state)
    assert result["input_type"] == "empty"


# --- validate_input ---


def test_validate_input_empty_is_invalid() -> None:
    """Entrada vazia resulta em validation_status='invalid'."""
    state = _make_state(raw_input="", input_type="empty")
    result = validate_input(state)
    assert result["validation_status"] == "invalid"
    assert result["repository_url"] is None
    assert result["local_files"] == []


def test_validate_input_invalid_url_scheme() -> None:
    """URL com esquema inválido resulta em validation_status='invalid'."""
    state = _make_state(raw_input="ftp://example.com/repo", input_type="url")
    result = validate_input(state)
    assert result["validation_status"] == "invalid"


def test_validate_input_valid_local_dir() -> None:
    """Diretório local existente resulta em validation_status='valid'."""
    with tempfile.TemporaryDirectory() as tmp:
        state = _make_state(raw_input=tmp, input_type="path")
        result = validate_input(state)
        assert result["validation_status"] == "valid"
        assert result["local_files"] == [str(Path(tmp).resolve())]


def test_validate_input_valid_md_file() -> None:
    """Arquivo .md existente resulta em validation_status='valid'."""
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write("# Test")
        f.flush()
        state = _make_state(raw_input=f.name, input_type="path")
        result = validate_input(state)
        assert result["validation_status"] == "valid"
        assert f.name in result["local_files"][0]

    Path(f.name).unlink()


def test_validate_input_invalid_extension() -> None:
    """Arquivo com extensão inválida resulta em validation_status='invalid'."""
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("hello")
        f.flush()
        state = _make_state(raw_input=f.name, input_type="path")
        result = validate_input(state)
        assert result["validation_status"] == "invalid"

    Path(f.name).unlink()


def test_validate_input_nonexistent_path() -> None:
    """Caminho inexistente resulta em validation_status='invalid'."""
    state = _make_state(raw_input="/caminho/que/nao/existe/arquivo.md", input_type="path")
    result = validate_input(state)
    assert result["validation_status"] == "invalid"


# --- Propriedade: receive_input só altera raw_input e input_type ---


@given(
    raw=st.text(min_size=0, max_size=100),
)
@settings(max_examples=50)
def test_receive_input_only_updates_own_fields(raw: str) -> None:
    """receive_input retorna apenas raw_input e input_type."""
    state = _make_state(raw_input=raw)
    result = receive_input(state)
    assert set(result.keys()) == {"raw_input", "input_type"}
