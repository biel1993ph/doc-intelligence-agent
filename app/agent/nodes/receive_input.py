"""Nó receive_input: registra entrada bruta no estado do agente."""

from pathlib import Path

from app.agent.state import AgentState


def receive_input(state: AgentState) -> dict:
    """Registra raw_input e identifica input_type.

    Classifica a entrada como:
    - "url": se parece com URL (http:// ou https://)
    - "path": se é um caminho de diretório/arquivo local
    - "empty": se a entrada está vazia

    Retorna apenas os campos que este nó é responsável por atualizar:
    raw_input e input_type.

    Args:
        state: Estado atual do agente.

    Returns:
        Dict parcial com raw_input e input_type.
    """
    raw = state.get("raw_input", "").strip()

    if not raw:
        return {"raw_input": raw, "input_type": "empty"}

    if raw.startswith("http://") or raw.startswith("https://"):
        input_type = "url"
    else:
        input_type = "path"

    return {"raw_input": raw, "input_type": input_type}
