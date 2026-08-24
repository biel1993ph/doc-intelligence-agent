"""Endpoint webhook para integração low-code/no-code (n8n, Make, Zapier).

Recebe URL de repositório via POST, executa análise e retorna resultado JSON.
A lógica principal permanece na aplicação Python — a ferramenta visual
apenas orquestra a chamada e processa a saída.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import run_agent

logger = logging.getLogger(__name__)

# FastAPI app para webhook
api_app = FastAPI(
    title="Doc Intelligence Agent API",
    description="API webhook para integração com ferramentas low-code (n8n, Make)",
    version="1.0.0",
)


class AnalyzeRequest(BaseModel):
    """Schema de entrada para requisição de análise."""

    url: str = Field(..., description="URL do repositório GitHub ou caminho local")
    input_type: Optional[str] = Field(default="", description="Tipo de entrada (opcional)")


class AnalyzeResponse(BaseModel):
    """Schema de saída com resultado da análise."""

    status: str = Field(..., description="Status da execução: success ou error")
    trace_id: str = Field(default="", description="ID de rastreamento da execução")
    score: Optional[int] = Field(default=None, description="Nota da documentação (0-10)")
    dimensions: Optional[dict] = Field(default=None, description="Avaliação por dimensão")
    strengths_count: int = Field(default=0, description="Quantidade de pontos fortes")
    issues_count: int = Field(default=0, description="Quantidade de problemas")
    report: Optional[str] = Field(default=None, description="Relatório completo em Markdown")
    errors: list[dict] = Field(default_factory=list, description="Erros encontrados")


@api_app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
    """Executa análise de documentação e retorna resultado estruturado.

    Este endpoint é o ponto de integração para ferramentas low-code:
    - n8n: HTTP Request node → POST /api/analyze
    - Make: HTTP module → POST /api/analyze
    - Zapier: Webhook action → POST /api/analyze

    Args:
        request: Corpo da requisição com URL do repositório.

    Returns:
        Resultado da análise em formato JSON estruturado.
    """
    if not request.url or not request.url.strip():
        raise HTTPException(status_code=400, detail="Campo 'url' é obrigatório e não pode estar vazio.")

    logger.info("Webhook: análise solicitada para %s", request.url[:100])

    try:
        result = run_agent(request.url.strip(), request.input_type or "")
    except Exception as e:
        logger.error("Webhook: erro na execução do agente: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro interno na análise: {e}")

    # Montar resposta estruturada
    analysis = result.get("analysis_result") or {}
    has_report = result.get("final_report") is not None

    response = AnalyzeResponse(
        status="success" if has_report else "error",
        trace_id=result.get("trace_id", ""),
        score=analysis.get("score"),
        dimensions=analysis.get("dimensions"),
        strengths_count=len(analysis.get("strengths", [])),
        issues_count=len(analysis.get("issues", [])),
        report=result.get("final_report"),
        errors=result.get("errors", []),
    )

    logger.info("Webhook: análise concluída. Score=%s, trace_id=%s", response.score, response.trace_id)
    return response


@api_app.get("/api/health")
def health_check() -> dict:
    """Health check para verificar se a API está disponível."""
    return {"status": "ok", "service": "doc-intelligence-agent"}
