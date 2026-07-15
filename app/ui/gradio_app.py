"""Interface Gradio para o agente de análise de documentação."""

import tempfile
from pathlib import Path

import gradio as gr

from app.agent.graph import run_agent
from app.services.sanitizer import sanitize_state


TIMEOUT_SECONDS = 120


def handle_submission(url: str, files: list | None) -> str:
    """Callback de submissão: valida entrada e executa o agente.

    Modos mutuamente exclusivos:
    - URL preenchida e sem arquivos → analisa repositório
    - Arquivos enviados e sem URL → analisa arquivos locais
    - Ambos preenchidos ou ambos vazios → erro

    Args:
        url: URL do repositório Git.
        files: Lista de arquivos .md enviados pelo upload.

    Returns:
        Relatório Markdown ou mensagem de erro.
    """
    has_url = bool(url and url.strip())
    has_files = bool(files and len(files) > 0)

    # Validação de modos mutuamente exclusivos
    if has_url and has_files:
        return "❌ **Erro:** Preencha apenas um campo — URL ou upload de arquivos, não ambos."

    if not has_url and not has_files:
        return "❌ **Erro:** Preencha pelo menos um campo — URL do repositório ou upload de arquivos."

    # Modo URL
    if has_url:
        raw_input = url.strip()
    else:
        # Modo arquivos: copiar para diretório temporário
        tmp_dir = tempfile.mkdtemp(prefix="doc_intel_upload_")
        for file_path in files:
            src = Path(file_path)
            if src.suffix.lower() in (".md", ".markdown"):
                dst = Path(tmp_dir) / src.name
                dst.write_bytes(src.read_bytes())

        raw_input = tmp_dir

    # Executar agente
    try:
        result = run_agent(raw_input)
    except Exception as e:
        return f"❌ **Erro inesperado:** {e}"

    # Sanitizar estado
    result = sanitize_state(result)

    # Verificar resultado
    if result.get("final_report"):
        return result["final_report"]

    # Sem relatório: mostrar erros
    errors = result.get("errors", [])
    validation_msg = result.get("validation_message", "")

    output_parts = []

    if validation_msg:
        output_parts.append(f"⚠️ **Validação:** {validation_msg}")

    if errors:
        output_parts.append("\n**Erros encontrados:**")
        for error in errors:
            node = error.get("node", "?")
            msg = error.get("message", "Erro desconhecido")
            output_parts.append(f"- `[{node}]` {msg}")

    if not output_parts:
        output_parts.append("❌ Não foi possível gerar o relatório. Verifique a entrada.")

    return "\n\n".join(output_parts)


def create_app() -> gr.Blocks:
    """Cria e retorna a aplicação Gradio.

    Layout:
    - Campo de texto para URL
    - Upload de arquivos .md (máximo 10)
    - Botão de análise
    - Área de resultado com renderização Markdown

    Returns:
        Instância gr.Blocks configurada.
    """
    with gr.Blocks(title="Doc Intelligence Agent") as app:
        gr.Markdown("# 📄 Doc Intelligence Agent")
        gr.Markdown("Analise a qualidade da documentação de um repositório Git ou arquivos Markdown locais.")

        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(
                    label="URL do Repositório Git",
                    placeholder="https://github.com/user/repo",
                    lines=1,
                )
                file_input = gr.File(
                    label="Upload de Arquivos Markdown",
                    file_count="multiple",
                    file_types=[".md", ".markdown"],
                    type="filepath",
                )
                submit_btn = gr.Button("🔍 Analisar Documentação", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="Resultado da Análise")

        submit_btn.click(
            fn=handle_submission,
            inputs=[url_input, file_input],
            outputs=output,
        )

    return app
