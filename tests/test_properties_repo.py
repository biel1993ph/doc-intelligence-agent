"""Testes de propriedade para ferramentas de repositório."""

from hypothesis import given, strategies as st, settings

from app.tools.repo_tools import validate_repository_url


# Estratégia: URLs com esquemas inválidos (não http/https)
invalid_schemes = st.sampled_from(
    ["ftp", "ssh", "git", "file", "", "mailto", "telnet"]
)


@given(
    scheme=invalid_schemes,
    host=st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and "/" not in x),
    path=st.text(min_size=0, max_size=30).filter(lambda x: " " not in x),
)
@settings(max_examples=100)
def test_invalid_scheme_rejected(scheme: str, host: str, path: str) -> None:
    """URLs com esquema diferente de http/https são sempre rejeitadas."""
    url = f"{scheme}://{host}/{path}"
    valid, message = validate_repository_url(url)
    assert valid is False, f"URL deveria ser inválida: {url}"


@given(
    suffix=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
)
@settings(max_examples=50)
def test_missing_host_rejected(suffix: str) -> None:
    """URLs sem host válido são rejeitadas."""
    url = f"https:///{suffix}"
    valid, message = validate_repository_url(url)
    assert valid is False, f"URL sem host deveria ser inválida: {url}"


# Estratégia: extensões de arquivo para teste de filtro markdown
valid_extensions = st.sampled_from([".md", ".markdown"])
invalid_extensions = st.sampled_from(
    [".txt", ".py", ".js", ".html", ".css", ".json", ".yml", ".xml", ".rst", ".doc"]
)


def is_markdown_file(filename: str) -> bool:
    """Verifica se o arquivo é markdown válido."""
    return filename.endswith((".md", ".markdown"))


@given(
    name=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N")),
        min_size=1,
        max_size=20,
    ),
    ext=valid_extensions,
)
@settings(max_examples=100)
def test_valid_markdown_extensions_accepted(name: str, ext: str) -> None:
    """Apenas extensões .md e .markdown são aceitas como markdown."""
    filename = f"{name}{ext}"
    assert is_markdown_file(filename), f"{filename} deveria ser aceito como markdown"


@given(
    name=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N")),
        min_size=1,
        max_size=20,
    ),
    ext=invalid_extensions,
)
@settings(max_examples=100)
def test_invalid_extensions_rejected(name: str, ext: str) -> None:
    """Extensões não-markdown são rejeitadas."""
    filename = f"{name}{ext}"
    assert not is_markdown_file(filename), f"{filename} não deveria ser aceito como markdown"
