"""Definição e compilação do grafo LangGraph do agente.

Fluxo com paralelização e observabilidade:
    receive_input → validate_input → discover_docs
        → [read_readme, read_prd_docs] (paralelo / fan-out)
        → merge_docs (fan-in / join)
        → analyze_docs → build_report → present_result

Cada nó é instrumentado com logs estruturados (trace_id, duration_ms).
"""

import traceback

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
from app.services.logger import (
    generate_trace_id,
    get_logger,
    log_node_start,
    log_node_end,
    log_audit_entry,
    measure_duration,
)

logger = get_logger("agent.graph")


def _instrument_node(node_fn, node_name: str):
    """Wrapper que instrumenta um nó com logging e timing.

    Registra entrada/saída, duration_ms e trace_id para cada execução.
    Adiciona timing ao campo node_timings do state.
    """

    def instrumented(state: AgentState) -> dict:
        trace_id = state.get("trace_id", "unknown")

        log_node_start(logger, node_name, trace_id)

        with measure_duration() as timer:
            try:
                result = node_fn(state)
            except Exception as e:
                duration_ms = timer["duration_ms"]
                log_node_end(
                    logger, node_name, trace_id, duration_ms,
                    success=False, error=str(e),
                )
                logger.error(
                    "node_exception",
                    node=node_name,
                    trace_id=trace_id,
                    exc_info=traceback.format_exc(),
                )
                # Re-raise para que o grafo trate o erro
                raise

        duration_ms = timer["duration_ms"]
        log_node_end(logger, node_name, trace_id, duration_ms)

        # Adicionar timing ao resultado
        if result is None:
            result = {}

        timing_entry = {
            "node": node_name,
            "duration_ms": duration_ms,
        }
        result.setdefault("node_timings", []).append(timing_entry)

        return result

    return instrumented


def _should_continue_after_validation(state: AgentState) -> str:
    """Roteamento condicional após validate_input."""
    if state.get("validation_status") == "invalid":
        trace_id = state.get("trace_id", "unknown")
        log_audit_entry(logger, trace_id, "routing_decision", decision="END", reason="validation_invalid")
        return END
    return "discover_docs"


def _should_continue_after_discovery(state: AgentState) -> str:
    """Roteamento condicional após discover_docs."""
    if not state.get("discovered_files"):
        trace_id = state.get("trace_id", "unknown")
        log_audit_entry(logger, trace_id, "routing_decision", decision="END", reason="no_files_discovered")
        return END
    return "read_readme"


def _should_continue_after_merge(state: AgentState) -> str:
    """Roteamento condicional após merge_docs."""
    if not state.get("merged_context"):
        trace_id = state.get("trace_id", "unknown")
        log_audit_entry(logger, trace_id, "routing_decision", decision="END", reason="no_merged_context")
        return END
    return "analyze_docs"


def build_graph() -> StateGraph:
    """Constrói e compila o grafo LangGraph com paralelização e observabilidade.

    Cada nó é instrumentado com logging estruturado que registra:
    - trace_id para correlação
    - timestamp de entrada/saída
    - duration_ms para análise de latência

    Returns:
        Grafo compilado pronto para execução.
    """
    graph = StateGraph(AgentState)

    # Adicionar nós instrumentados
    graph.add_node("receive_input", _instrument_node(receive_input, "receive_input"))
    graph.add_node("validate_input", _instrument_node(validate_input, "validate_input"))
    graph.add_node("discover_docs", _instrument_node(discover_docs, "discover_docs"))
    graph.add_node("read_readme", _instrument_node(read_readme, "read_readme"))
    graph.add_node("read_prd_docs", _instrument_node(read_prd_docs, "read_prd_docs"))
    graph.add_node("merge_docs", _instrument_node(merge_docs, "merge_docs"))
    graph.add_node("analyze_docs", _instrument_node(analyze_docs, "analyze_docs"))
    graph.add_node("build_report", _instrument_node(build_report, "build_report"))
    graph.add_node("present_result", _instrument_node(present_result, "present_result"))

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

    Gera trace_id único para correlação de toda a execução.
    Registra auditoria de entrada e resultado final.

    Args:
        raw_input: Entrada bruta do usuário (URL ou caminho).
        input_type: Tipo de entrada (opcional, será detectado pelo receive_input).

    Returns:
        Estado final do agente após execução completa.
    """
    trace_id = generate_trace_id()

    log_audit_entry(
        logger, trace_id, "execution_start",
        raw_input=raw_input[:200],  # Truncar para segurança
        input_type=input_type,
    )

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
        "trace_id": trace_id,
        "node_timings": [],
    }

    with measure_duration() as total_timer:
        result = agent_graph.invoke(initial_state)

    total_duration = total_timer["duration_ms"]

    log_audit_entry(
        logger, trace_id, "execution_end",
        total_duration_ms=total_duration,
        validation_status=result.get("validation_status"),
        files_discovered=len(result.get("discovered_files", [])),
        has_report=result.get("final_report") is not None,
        error_count=len(result.get("errors", [])),
    )

    return result
