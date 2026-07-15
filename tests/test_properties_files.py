"""Testes de propriedade para ferramentas de arquivo e texto."""

import tempfile
from pathlib import Path

from hypothesis import given, strategies as st, settings, assume

from app.tools.file_tools import find_documentation_files, PRIORITY_PATTERNS, VALID_EXTENSIONS
from app.tools.text_tools import normalize_document_text


# --- Testes de normalização (idempotência) ---


@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z", "S")),
        min_size=0,
        max_size=500,
    ),
)
@settings(max_examples=200)
def test_normalize_is_idempotent(text: str) -> None:
    """Normalizar um texto duas vezes produz o mesmo resultado."""
    once = normalize_document_text(text)
    twice = normalize_document_text(once)
    assert once == twice, f"Normalização não é idempotente para: {repr(text)}"


@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
        min_size=1,
        max_size=300,
    ),
)
@settings(max_examples=100)
def test_normalize_no_consecutive_blank_lines(text: str) -> None:
    """Texto normalizado nunca contém mais de uma linha em branco consecutiva."""
    result = normalize_document_text(text)
    lines = result.split("\n")
    for i in range(len(lines) - 1):
        assert not (lines[i] == "" and lines[i + 1] == ""), (
            f"Linhas em branco consecutivas encontradas na posição {i}"
        )


@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
        min_size=1,
        max_size=200,
    ),
)
@settings(max_examples=100)
def test_normalize_no_trailing_spaces(text: str) -> None:
    """Texto normalizado não tem espaços no início/fim de linhas."""
    result = normalize_document_text(text)
    for line in result.split("\n"):
        assert line == line.strip(), f"Linha com espaços: '{line}'"


# --- Testes de descoberta (prioridade e deduplicação) ---


def test_discovery_respects_priority_order() -> None:
    """Arquivos descobertos respeitam a ordem de prioridade definida."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Criar estrutura docs/
        (root / "docs").mkdir()

        # Criar arquivos em ordem inversa de prioridade
        files_to_create = ["docs/prd.md", "product_requirements.md", "docs/README.md", "PRD.md", "README.md"]
        for f in files_to_create:
            (root / f).write_text(f"# {f}", encoding="utf-8")

        result = find_documentation_files(root)

        # Resultado deve respeitar a ordem de PRIORITY_PATTERNS
        assert result == PRIORITY_PATTERNS


def test_discovery_deduplicates_case_insensitive() -> None:
    """Deduplicação é case-insensitive."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Criar README.md e readme.md (mesmo arquivo em case-insensitive)
        (root / "README.md").write_text("# Hello", encoding="utf-8")

        result = find_documentation_files(root)

        # Verificar que não há duplicatas case-insensitive
        lower_results = [r.lower() for r in result]
        assert len(lower_results) == len(set(lower_results)), "Duplicatas case-insensitive encontradas"


def test_discovery_max_five_files() -> None:
    """Descoberta retorna no máximo 5 arquivos."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()

        # Criar mais de 5 arquivos markdown
        for i in range(10):
            (root / f"doc_{i}.md").write_text(f"# Doc {i}", encoding="utf-8")

        result = find_documentation_files(root)
        assert len(result) <= 5, f"Retornou {len(result)} arquivos, máximo é 5"
