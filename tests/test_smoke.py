"""Smoke tests: importação, estrutura e dependências."""

import importlib
from pathlib import Path


# --- Importação isolada de cada módulo ---


def test_import_agent_state() -> None:
    """Importa app.agent.state sem erros."""
    mod = importlib.import_module("app.agent.state")
    assert hasattr(mod, "AgentState")


def test_import_agent_graph() -> None:
    """Importa app.agent.graph sem erros."""
    mod = importlib.import_module("app.agent.graph")
    assert hasattr(mod, "build_graph")
    assert hasattr(mod, "run_agent")


def test_import_nodes() -> None:
    """Importa app.agent.nodes sem erros."""
    mod = importlib.import_module("app.agent.nodes")
    assert hasattr(mod, "receive_input")
    assert hasattr(mod, "validate_input")
    assert hasattr(mod, "discover_docs")
    assert hasattr(mod, "read_docs")
    assert hasattr(mod, "analyze_docs")
    assert hasattr(mod, "build_report")
    assert hasattr(mod, "present_result")


def test_import_repo_tools() -> None:
    """Importa app.tools.repo_tools sem erros."""
    mod = importlib.import_module("app.tools.repo_tools")
    assert hasattr(mod, "validate_repository_url")
    assert hasattr(mod, "clone_or_open_repository")


def test_import_file_tools() -> None:
    """Importa app.tools.file_tools sem erros."""
    mod = importlib.import_module("app.tools.file_tools")
    assert hasattr(mod, "find_documentation_files")
    assert hasattr(mod, "read_markdown_file")


def test_import_text_tools() -> None:
    """Importa app.tools.text_tools sem erros."""
    mod = importlib.import_module("app.tools.text_tools")
    assert hasattr(mod, "normalize_document_text")


def test_import_report_service() -> None:
    """Importa app.services.report_service sem erros."""
    mod = importlib.import_module("app.services.report_service")
    assert hasattr(mod, "generate_report_markdown")


def test_import_sanitizer() -> None:
    """Importa app.services.sanitizer sem erros."""
    mod = importlib.import_module("app.services.sanitizer")
    assert hasattr(mod, "sanitize_text")
    assert hasattr(mod, "sanitize_state")


def test_import_gradio_app() -> None:
    """Importa app.ui.gradio_app sem erros."""
    mod = importlib.import_module("app.ui.gradio_app")
    assert hasattr(mod, "create_app")
    assert hasattr(mod, "handle_submission")


# --- AgentState contém todos os 13 campos ---


def test_agent_state_has_13_fields() -> None:
    """AgentState contém exatamente 17 campos tipados."""
    from app.agent.state import AgentState

    expected_fields = {
        "raw_input", "input_type", "validation_status", "validation_message",
        "repository_url", "local_files", "discovered_files", "readme_content",
        "prd_content", "merged_context", "analysis_result", "final_report", "errors",
        "trace_id", "node_timings", "repository_metadata", "analysis_history",
    }

    assert set(AgentState.__annotations__.keys()) == expected_fields
    assert len(AgentState.__annotations__) == 17


# --- Ausência de dependências circulares ---


def test_no_circular_dependencies() -> None:
    """Importação completa do app não causa ImportError circular."""
    # Se houver dependência circular, isso falhará com ImportError
    import app.agent.graph
    import app.agent.nodes
    import app.tools.repo_tools
    import app.tools.file_tools
    import app.tools.text_tools
    import app.services.report_service
    import app.services.sanitizer
    import app.ui.gradio_app


# --- .env.example existe ---


def test_env_example_exists() -> None:
    """.env.example existe na raiz do projeto."""
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"
    assert env_example.exists(), f".env.example não encontrado em {project_root}"


def test_env_example_has_required_vars() -> None:
    """.env.example contém as variáveis documentadas."""
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"
    content = env_example.read_text()

    assert "OPENAI_API_KEY" in content
    assert "LLM_MODEL" in content
    assert "LOG_LEVEL" in content
