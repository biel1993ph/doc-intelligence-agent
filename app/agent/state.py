"""Estado tipado do agente de análise de documentação."""

from typing import TypedDict


class ErrorEntry(TypedDict):
    """Entrada de erro registrada por qualquer nó do grafo."""

    node: str
    message: str


class AgentState(TypedDict):
    """Estado compartilhado entre os nós do grafo LangGraph.

    Contém os 13 campos tipados que representam o ciclo completo
    de análise de documentação de software.
    """

    raw_input: str
    input_type: str
    validation_status: str
    validation_message: str
    repository_url: str | None
    local_files: list[str]
    discovered_files: list[str]
    readme_content: str | None
    prd_content: str | None
    merged_context: str | None
    analysis_result: dict | None
    final_report: str | None
    errors: list[ErrorEntry]
