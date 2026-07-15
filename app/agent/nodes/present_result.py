"""Nó present_result: nó terminal do grafo, não altera estado."""

from app.agent.state import AgentState


def present_result(state: AgentState) -> dict:
    """Nó terminal — retorna estado sem alterações.

    Este nó existe para marcar o fim do grafo.
    O resultado final já está disponível em final_report.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict vazio (não altera estado).
    """
    return {}
