"""Serviço de memória: histórico de análises persistido em SQLite.

Permite ao agente recuperar informações de execuções anteriores
do mesmo repositório, possibilitando comparação de evolução.
"""

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

# Diretório padrão para o banco de dados
_DEFAULT_DB_DIR = "data"
_DEFAULT_DB_NAME = "analysis_history.db"


class AnalysisRecord(TypedDict):
    """Registro de uma análise anterior."""

    id: int
    source_key: str
    raw_input: str
    analyzed_at: str
    score: int
    dimensions: dict
    findings_count: int
    strengths_count: int


def _get_db_path() -> str:
    """Retorna caminho do banco SQLite, criando diretório se necessário."""
    db_dir = os.environ.get("ANALYSIS_DB_DIR", _DEFAULT_DB_DIR)
    path = Path(db_dir)
    path.mkdir(parents=True, exist_ok=True)
    return str(path / _DEFAULT_DB_NAME)


def _get_connection() -> sqlite3.Connection:
    """Abre conexão SQLite e cria tabela se não existir."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_key TEXT NOT NULL,
            raw_input TEXT NOT NULL,
            analyzed_at TEXT NOT NULL,
            score INTEGER NOT NULL,
            dimensions TEXT NOT NULL,
            findings_count INTEGER NOT NULL DEFAULT 0,
            strengths_count INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_source_key
        ON analysis_history(source_key)
    """)
    conn.commit()
    return conn


def generate_source_key(raw_input: str) -> str:
    """Gera chave única para o repositório/diretório analisado.

    Usa hash MD5 do raw_input normalizado para agrupar execuções
    do mesmo repositório/caminho.

    Args:
        raw_input: Entrada bruta (URL ou caminho).

    Returns:
        Hash MD5 como string hex.
    """
    normalized = raw_input.strip().rstrip("/").lower()
    return hashlib.md5(normalized.encode()).hexdigest()


def save_analysis(raw_input: str, analysis_result: dict) -> None:
    """Persiste o resultado de uma análise no histórico.

    Args:
        raw_input: Entrada original (URL ou caminho).
        analysis_result: Resultado completo da análise.
    """
    source_key = generate_source_key(raw_input)
    score = analysis_result.get("score", 0)
    dimensions = analysis_result.get("dimensions", {})
    findings_count = len(analysis_result.get("issues", []))
    strengths_count = len(analysis_result.get("strengths", []))
    analyzed_at = datetime.now(timezone.utc).isoformat()

    try:
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO analysis_history
                (source_key, raw_input, analyzed_at, score, dimensions, findings_count, strengths_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (source_key, raw_input, analyzed_at, score, json.dumps(dimensions), findings_count, strengths_count),
        )
        conn.commit()
        conn.close()
        logger.info("Análise salva no histórico: source_key=%s, score=%d", source_key, score)
    except sqlite3.Error as e:
        logger.warning("Erro ao salvar histórico: %s", e)


def get_history(raw_input: str, limit: int = 5) -> list[AnalysisRecord]:
    """Recupera histórico de análises anteriores do mesmo repositório.

    Args:
        raw_input: Entrada original (URL ou caminho).
        limit: Número máximo de registros a retornar.

    Returns:
        Lista de registros ordenados do mais recente ao mais antigo.
    """
    source_key = generate_source_key(raw_input)

    try:
        conn = _get_connection()
        cursor = conn.execute(
            """
            SELECT id, source_key, raw_input, analyzed_at, score, dimensions,
                   findings_count, strengths_count
            FROM analysis_history
            WHERE source_key = ?
            ORDER BY analyzed_at DESC
            LIMIT ?
            """,
            (source_key, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            records.append({
                "id": row["id"],
                "source_key": row["source_key"],
                "raw_input": row["raw_input"],
                "analyzed_at": row["analyzed_at"],
                "score": row["score"],
                "dimensions": json.loads(row["dimensions"]),
                "findings_count": row["findings_count"],
                "strengths_count": row["strengths_count"],
            })

        return records
    except sqlite3.Error as e:
        logger.warning("Erro ao recuperar histórico: %s", e)
        return []
