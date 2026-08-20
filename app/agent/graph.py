"""Definição e compilação do grafo LangGraph do agente.

Fluxo com paralelização:
    receive_input → validate_input → discover_docs
        → [read_readme, read_prd_docs] (paralelo / fan-out)
        → merge_docs (fan-in / join)
        → analyze_docs → build_report → present_result
"""

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    receive_input,
    validate_input,
    discover_docs,
    read_readme,
    read_prd_docs,
    merge_docs,
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
    return "read_readme"


def _should_continue_after_merge(state: AgentState) -> str:
    """Roteamento condicional após merge_docs."""
    if not state.get("merged_context"):
        return END
    return "analyze_docs"


def build_graph() -> StateGraph:
    """Constrói e compila o grafo LangGraph com paralelização.

    Sequência com fan-out/fan-in:
        receive_input → validate_input → discover_docs
            → [read_readme, read_prd_docs] (fan-out paralelo)
            → merge_docs (fan-in / join)
            → analyze_docs → build_report → present_result

    Roteamento condicional:
        - validate_input → END se invalid
        - discover_docs → END se discovered_files vazio
        - merge_docs → END se merged_context vazio

    Returns:
        Grafo compilado pronto para execução.
    """
    graph = StateGraph(AgentState)

    # Adicionar nós
    graph.add_node("receive_input", receive_input)
    graph.add_node("validate_input", validate_input)
    graph.add_node("discover_docs", discover_docs)
    graph.add_node("read_readme", read_readme)
    graph.add_node("read_prd_docs", read_prd_docs)
    graph.add_node("merge_docs", merge_docs)
    graph.add_node("analyze_docs", analyze_docs)
    graph.add_node("build_report", build_report)
    graph.add_node("present_result", present_result)

    # Entry point
    graph.set_entry_point("receive_input")

    # Edges sequenciais iniciais
    graph.add_edge("receive_input", "validate_input")

    # Roteamento condicional após validação
    graph.add_conditional_edges(
        "validate_input",
        _should_continue_after_validation,
    )

    # Roteamento condicional após descoberta → fan-out
    graph.add_conditional_edges(
        "discover_docs",
        _should_continue_after_discovery,
    )

    # Fan-out: discover_docs → [read_readme, read_prd_docs] (paralelo)
    # Ambos os nós executam simultaneamente
    graph.add_edge("discover_docs", "read_prd_docs")

    # Fan-in: [read_readme, read_prd_docs] → merge_docs
    graph.add_edge("read_readme", "merge_docs")
    graph.add_edge("read_prd_docs", "merge_docs")

    # Roteamento condicional após merge
    graph.add_conditional_edges(
        "merge_docs",
        _should_continue_after_merge,
    )

    # Edges sequenciais finais
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
