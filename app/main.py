"""Ponto de entrada da aplicação Doc Intelligence Agent."""

import sys

from app.ui.gradio_app import create_app


def main() -> None:
    """Inicializa e executa a aplicação Gradio."""
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)


def run_api() -> None:
    """Inicializa e executa a API webhook (FastAPI/Uvicorn).

    Endpoint disponível em http://localhost:8000/api/analyze
    Para integração com n8n, Make ou outras ferramentas low-code.
    """
    import uvicorn

    from app.api.webhook import api_app

    uvicorn.run(api_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        run_api()
    else:
        main()
