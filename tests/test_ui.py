"""Testes para interface Gradio e handle_submission."""

import tempfile
from pathlib import Path

from app.ui.gradio_app import handle_submission, create_app


def test_handle_submission_all_empty() -> None:
    """Todos vazios retorna erro."""
    result = handle_submission("", "", None)
    assert "Erro" in result
    assert "pelo menos um campo" in result


def test_handle_submission_url_and_files_filled() -> None:
    """URL e arquivos preenchidos retorna erro de modo exclusivo."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(b"# Test")
        f.flush()
        result = handle_submission("https://github.com/user/repo", "", [f.name])
        assert "Erro" in result
        assert "apenas um campo" in result

    Path(f.name).unlink()


def test_handle_submission_url_and_path_filled() -> None:
    """URL e caminho local preenchidos retorna erro de modo exclusivo."""
    result = handle_submission("https://github.com/user/repo", "/tmp/projeto", None)
    assert "Erro" in result
    assert "apenas um campo" in result


def test_handle_submission_path_and_files_filled() -> None:
    """Caminho local e arquivos preenchidos retorna erro de modo exclusivo."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(b"# Test")
        f.flush()
        result = handle_submission("", "/tmp/projeto", [f.name])
        assert "Erro" in result
        assert "apenas um campo" in result

    Path(f.name).unlink()


def test_handle_submission_invalid_url() -> None:
    """URL inválida retorna mensagem de validação."""
    result = handle_submission("ftp://invalid.com", "", None)
    # Deve mostrar mensagem de validação ou erro
    assert "inválid" in result.lower() or "Erro" in result or "Validação" in result


def test_handle_submission_local_dir_with_readme() -> None:
    """Diretório local via campo URL (path) produz relatório."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text(
            "# Projeto\n\nDescrição suficiente para análise completa.\n\n"
            "## Instalação\n\npip install projeto\n\n## Uso\n\nExemplo aqui.\n",
            encoding="utf-8",
        )
        result = handle_submission("", tmp, None)
        assert "Relatório" in result


def test_handle_submission_local_path_field() -> None:
    """Caminho local via campo dedicado produz relatório."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text(
            "# Projeto\n\nDescrição suficiente para análise completa.\n\n"
            "## Instalação\n\npip install projeto\n\n## Uso\n\nExemplo aqui.\n",
            encoding="utf-8",
        )
        result = handle_submission("", tmp, None)
        assert "Relatório" in result


def test_handle_submission_upload_multiple_files() -> None:
    """Upload de múltiplos arquivos funciona."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text("# README\n\nConteúdo do readme.\n", encoding="utf-8")
        prd = Path(tmp) / "PRD.md"
        prd.write_text("# PRD\n\nConteúdo do PRD.\n", encoding="utf-8")

        result = handle_submission("", "", [str(readme), str(prd)])
        # Deve processar sem erro de modo exclusivo
        assert "apenas um campo" not in result


def test_create_app_returns_blocks() -> None:
    """create_app retorna instância Gradio Blocks."""
    app = create_app()
    assert app is not None
