"""Definição e compilação do grafo LangGraph do agente."""

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    receive_input,
    validate_input,
    discover_docs,
    read_docs,
    analyze_docs,
    build_report,
    present_result,
)


def _should_continue_after_validation(state: AgentState) -> str:
    """Roteamento condicional após validate_input."""
    if state.get("validation_status") == "invalid":
        return END
    return "discover_docs"


def _should_continue_after_discovery(state: AgentState) -> str:
    """Roteamento condicional após discover_docs."""
    if not state.get("discovered_files"):
        return END
    return "read_docs"


def _should_continue_after_read(state: AgentState) -> str:
    """Roteamento condicional após read_docs."""
    if not state.get("merged_context"):
        return END
    return "analyze_docs"


def build_graph() -> StateGraph:
    """Constrói e compila o grafo LangGraph com os 7 nós.

    Sequência: receive_input → validate_input → discover_docs →
    read_docs → analyze_docs → build_report → present_result

    Roteamento condicional:
    - validate_input → END se invalid
    - discover_docs → END se discovered_files vazio
    - read_docs → END se merged_context vazio

    Returns:
        Grafo compilado pronto para execução.
    """
    graph = StateGraph(AgentState)

    # Adicionar nós
    graph.add_node("receive_input", receive_input)
    graph.add_node("validate_input", validate_input)
    graph.add_node("discover_docs", discover_docs)
    graph.add_node("read_docs", read_docs)
    graph.add_node("analyze_docs", analyze_docs)
    graph.add_node("build_report", build_report)
    graph.add_node("present_result", present_result)

    # Entry point
    graph.set_entry_point("receive_input")

    # Edges sequenciais
    graph.add_edge("receive_input", "validate_input")

    # Edges condicionais
    graph.add_conditional_edges(
        "validate_input",
        _should_continue_after_validation,
    )

    graph.add_conditional_edges(
        "discover_docs",
        _should_continue_after_discovery,
    )

    graph.add_conditional_edges(
        "read_docs",
        _should_continue_after_read,
    )

    # Edges sequenciais restantes
    graph.add_edge("analyze_docs", "build_report")
    graph.add_edge("build_report", "present_result")
    graph.add_edge("present_result", END)

    return graph.compile()


# Grafo compilado (singleton)
agent_graph = build_graph()


def run_agent(raw_input: str, input_type: str = "") -> AgentState:
    """Executa o grafo do agente e retorna o estado final.

    Args:
        raw_input: Entrada bruta do usuário (URL ou caminho).
        input_type: Tipo de entrada (opcional, será detectado pelo receive_input).

    Returns:
        Estado final do agente após execução completa.
    """
    initial_state: AgentState = {
        "raw_input": raw_input,
        "input_type": input_type,
        "validation_status": "",
        "validation_message": "",
        "repository_url": None,
        "local_files": [],
        "discovered_files": [],
        "readme_content": None,
        "prd_content": None,
        "merged_context": None,
        "analysis_result": None,
        "final_report": None,
        "errors": [],
    }

    result = agent_graph.invoke(initial_state)
    return result
