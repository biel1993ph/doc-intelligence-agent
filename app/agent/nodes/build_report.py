"""Nó build_report: gera relatório final Markdown."""

from app.agent.state import AgentState
from app.services.report_service import generate_report_markdown


def build_report(state: AgentState) -> dict:
    """Invoca o serviço de geração de relatório e registra final_report.

    Trata analysis_result ausente como erro.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com final_report e erros.
    """
    analysis_result = state.get("analysis_result")
    discovered_files = state.get("discovered_files", [])
    repository_metadata = state.get("repository_metadata")
    errors: list[dict] = []

    if not analysis_result:
        errors.append({
            "node": "build_report",
            "message": "analysis_result ausente — impossível gerar relatório.",
        })
        return {
            "final_report": None,
            "errors": errors,
        }

    report = generate_report_markdown(analysis_result, discovered_files, repository_metadata)

    return {
        "final_report": report,
        "errors": errors,
    }
