"""Ferramentas de descoberta e leitura de arquivos de documentação."""

from pathlib import Path


# Prioridade de busca de documentação (ordem importa)
PRIORITY_PATTERNS: list[str] = [
    "README.md",
    "PRD.md",
    "docs/README.md",
    "product_requirements.md",
    "docs/prd.md",
]

MAX_DISCOVERED_FILES = 5
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
VALID_EXTENSIONS = (".md", ".markdown")


def find_documentation_files(root_path: str | Path) -> list[str]:
    """Busca arquivos de documentação por prioridade no diretório raiz.

    Prioridade: README.md > PRD.md > docs/README.md >
    product_requirements.md > docs/prd.md.
    Máximo 5 resultados. Deduplicação case-insensitive.

    Args:
        root_path: Caminho raiz do repositório/diretório.

    Returns:
        Lista de caminhos relativos dos arquivos encontrados.
    """
    root = Path(root_path)
    if not root.exists() or not root.is_dir():
        return []

    found: list[str] = []
    seen_lower: set[str] = set()

    # Busca por prioridade definida
    for pattern in PRIORITY_PATTERNS:
        candidate = root / pattern
        if candidate.exists() and candidate.is_file():
            relative = str(candidate.relative_to(root))
            if relative.lower() not in seen_lower:
                seen_lower.add(relative.lower())
                found.append(relative)
                if len(found) >= MAX_DISCOVERED_FILES:
                    return found

    # Busca adicional por extensão em todo o diretório
    if len(found) < MAX_DISCOVERED_FILES:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
                relative = str(path.relative_to(root))
                if relative.lower() not in seen_lower:
                    seen_lower.add(relative.lower())
                    found.append(relative)
                    if len(found) >= MAX_DISCOVERED_FILES:
                        break

    return found


def read_markdown_file(file_path: str | Path) -> tuple[str | None, str | None]:
    """Lê um arquivo Markdown com limite de tamanho e fallback de encoding.

    Limite: 1 MB. Encoding: tenta UTF-8, fallback para Latin-1.

    Args:
        file_path: Caminho do arquivo a ser lido.

    Returns:
        Tupla (conteúdo, erro). Em sucesso, erro é None.
        Em falha, conteúdo é None e erro descreve o problema.
    """
    path = Path(file_path)

    if not path.exists():
        return None, f"Arquivo não encontrado: {file_path}"

    if not path.is_file():
        return None, f"Caminho não é um arquivo: {file_path}"

    if path.suffix.lower() not in VALID_EXTENSIONS:
        return None, f"Extensão inválida: {path.suffix}. Aceitas: {VALID_EXTENSIONS}"

    # Verificar tamanho
    try:
        size = path.stat().st_size
    except OSError as e:
        return None, f"Erro ao verificar tamanho: {e}"

    if size > MAX_FILE_SIZE_BYTES:
        return None, f"Arquivo excede limite de 1 MB: {size} bytes"

    # Tentar leitura com UTF-8, fallback Latin-1
    try:
        content = path.read_text(encoding="utf-8")
        return content, None
    except UnicodeDecodeError:
        pass

    try:
        content = path.read_text(encoding="latin-1")
        return content, None
    except Exception as e:
        return None, f"Erro de leitura: {e}"
