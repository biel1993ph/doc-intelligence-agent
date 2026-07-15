"""Ponto de entrada da aplicação Doc Intelligence Agent."""

from app.ui.gradio_app import create_app


def main() -> None:
    """Inicializa e executa a aplicação Gradio."""
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
