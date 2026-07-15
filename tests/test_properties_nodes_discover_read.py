"""Testes de propriedade para nós discover_docs e read_docs."""

import tempfile
from pathlib import Path

from hypothesis import given, strategies as st, settings

from app.agent.nodes.discover_docs import discover_docs
from app.agent.nodes.read_docs import read_docs, MAX_FILES_PER_EXECUTION


def _make_state(**kwargs) -> dict:
    """Cria estado mínimo para testes."""
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


# --- discover_docs ---


def test_discover_docs_finds_readme_in_dir() -> None:
    """discover_docs encontra README.md em diretório local."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text("# Hello", encoding="utf-8")

        state = _make_state(local_files=[tmp])
        result = discover_docs(state)

        assert len(result["discovered_files"]) >= 1
        assert any("README.md" in f for f in result["discovered_files"])


def test_discover_docs_no_source_errors() -> None:
    """discover_docs sem URL nem local_files registra erro."""
    state = _make_state(repository_url=None, local_files=[])
    result = discover_docs(state)

    assert result["discovered_files"] == []
    assert len(result["errors"]) > 0
    assert result["errors"][-1]["node"] == "discover_docs"


def test_discover_docs_empty_dir_errors() -> None:
    """discover_docs em diretório vazio registra erro."""
    with tempfile.TemporaryDirectory() as tmp:
        state = _make_state(local_files=[tmp])
        result = discover_docs(state)

        assert result["discovered_files"] == []
        assert any(e["node"] == "discover_docs" for e in result["errors"])


def test_discover_docs_single_md_file() -> None:
    """discover_docs com arquivo .md individual retorna caminho absoluto."""
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write("# Test")
        f.flush()
        state = _make_state(local_files=[f.name])
        result = discover_docs(state)

        assert len(result["discovered_files"]) == 1
        assert Path(result["discovered_files"][0]).is_absolute()

    Path(f.name).unlink()


# --- read_docs ---


def test_read_docs_identifies_readme() -> None:
    """read_docs identifica README e armazena em readme_content."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text("# My Project\n\nDescription here.", encoding="utf-8")

        state = _make_state(discovered_files=[str(readme)])
        result = read_docs(state)

        assert result["readme_content"] is not None
        assert "My Project" in result["readme_content"]


def test_read_docs_identifies_prd() -> None:
    """read_docs identifica PRD e armazena em prd_content."""
    with tempfile.TemporaryDirectory() as tmp:
        prd = Path(tmp) / "PRD.md"
        prd.write_text("# Product Requirements\n\nFeatures.", encoding="utf-8")

        state = _make_state(discovered_files=[str(prd)])
        result = read_docs(state)

        assert result["prd_content"] is not None
        assert "Product Requirements" in result["prd_content"]


def test_read_docs_merged_context_has_traceability() -> None:
    """merged_context contém cabeçalhos de rastreabilidade com nome do arquivo."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text("# Hello", encoding="utf-8")

        prd = Path(tmp) / "PRD.md"
        prd.write_text("# PRD", encoding="utf-8")

        state = _make_state(discovered_files=[str(readme), str(prd)])
        result = read_docs(state)

        assert result["merged_context"] is not None
        assert "--- Fonte: README.md ---" in result["merged_context"]
        assert "--- Fonte: PRD.md ---" in result["merged_context"]


def test_read_docs_respects_max_files_limit() -> None:
    """read_docs respeita limite de 20 arquivos."""
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i in range(25):
            f = Path(tmp) / f"doc_{i}.md"
            f.write_text(f"# Doc {i}", encoding="utf-8")
            files.append(str(f))

        state = _make_state(discovered_files=files)
        result = read_docs(state)

        # merged_context deve conter no máximo 20 fontes
        sources = result["merged_context"].count("--- Fonte:")
        assert sources <= MAX_FILES_PER_EXECUTION


def test_read_docs_empty_discovered_files_errors() -> None:
    """read_docs sem arquivos descobertos registra erro."""
    state = _make_state(discovered_files=[])
    result = read_docs(state)

    assert result["merged_context"] is None
    assert any(e["node"] == "read_docs" for e in result["errors"])


# --- Propriedade: contexto consolidado preserva conteúdo ---


@given(
    content=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P")),
        min_size=5,
        max_size=200,
    ),
)
@settings(max_examples=50)
def test_merged_context_preserves_content(content: str) -> None:
    """O conteúdo original aparece (normalizado) no merged_context."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text(content, encoding="utf-8")

        state = _make_state(discovered_files=[str(readme)])
        result = read_docs(state)

        if result["merged_context"]:
            # Pelo menos parte do conteúdo original deve estar presente
            # (normalização pode alterar espaços mas não o texto em si)
            words = [w for w in content.split() if len(w) > 2]
            if words:
                assert any(w in result["merged_context"] for w in words[:3])
