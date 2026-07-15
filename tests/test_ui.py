"""Testes para interface Gradio e handle_submission."""

import tempfile
from pathlib import Path

from app.ui.gradio_app import handle_submission, create_app


def test_handle_submission_both_empty() -> None:
    """Ambos vazios retorna erro."""
    result = handle_submission("", None)
    assert "Erro" in result
    assert "pelo menos um campo" in result


def test_handle_submission_both_filled() -> None:
    """Ambos preenchidos retorna erro de modo exclusivo."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(b"# Test")
        f.flush()
        result = handle_submission("https://github.com/user/repo", [f.name])
        assert "Erro" in result
        assert "não ambos" in result

    Path(f.name).unlink()


def test_handle_submission_invalid_url() -> None:
    """URL inválida retorna mensagem de validação."""
    result = handle_submission("ftp://invalid.com", None)
    # Deve mostrar mensagem de validação ou erro
    assert "inválid" in result.lower() or "Erro" in result or "Validação" in result


def test_handle_submission_local_dir_with_readme() -> None:
    """Diretório local com README produz relatório."""
    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "README.md"
        readme.write_text(
            "# Projeto\n\nDescrição suficiente para análise completa.\n\n"
            "## Instalação\n\npip install projeto\n\n## Uso\n\nExemplo aqui.\n",
            encoding="utf-8",
        )
        result = handle_submission(tmp, None)
        assert "Relatório" in result


def test_create_app_returns_blocks() -> None:
    """create_app retorna instância Gradio Blocks."""
    app = create_app()
    assert app is not None
