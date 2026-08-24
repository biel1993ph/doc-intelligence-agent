# Priorização de Testes por Risco

## Metodologia

Cada cenário de teste é avaliado com base em três critérios:
- **Impacto no usuário**: Consequência direta se o cenário falhar (Alto/Médio/Baixo)
- **Probabilidade de falha**: Chance de ocorrer em produção (Alta/Média/Baixa)
- **Severidade**: Gravidade do problema resultante (Crítica/Alta/Média/Baixa)

**Risco = Impacto × Probabilidade × Severidade**

## Cenários de Teste Existentes

| # | Cenário | Tipo | Impacto | Probabilidade | Severidade | Risco |
|---|---------|------|---------|---------------|------------|-------|
| 1 | Fluxo completo com README + PRD | E2E | Alto | Média | Crítica | **ALTO** |
| 2 | Input inválido não causa crash | E2E | Alto | Alta | Alta | **ALTO** |
| 3 | Base insuficiente limita nota a 3 | E2E | Médio | Média | Alta | **ALTO** |
| 4 | Prompt injection não altera comportamento | Security | Alto | Média | Crítica | **ALTO** |
| 5 | LLM fallback para heurística | Integration | Médio | Alta | Média | **MÉDIO** |
| 6 | Retry em chamadas HTTP | Integration | Médio | Média | Média | **MÉDIO** |
| 7 | Paralelização fan-out/fan-in funciona | Integration | Médio | Baixa | Alta | **MÉDIO** |
| 8 | Histórico de análises persiste | Integration | Baixo | Baixa | Média | **BAIXO** |
| 9 | Relatório contém todas as seções | E2E | Médio | Baixa | Média | **MÉDIO** |
| 10 | Observabilidade (trace_id + timings) | E2E | Baixo | Baixa | Baixa | **BAIXO** |

## Teste Prioritário Selecionado

### Cenário #1 — Fluxo completo com README + PRD

**Justificativa de priorização:**

1. **Impacto no usuário: ALTO** — Este é o cenário principal de uso da aplicação. Se falhar, nenhum usuário consegue obter uma análise de documentação. Afeta 100% dos usuários.

2. **Probabilidade de falha: MÉDIA** — O fluxo envolve 9 nós do grafo LangGraph, incluindo paralelização e múltiplas dependências (filesystem, parsing, LLM/heurística). Qualquer alteração em nós intermediários pode introduzir regressão.

3. **Severidade: CRÍTICA** — Falha completa do produto. Sem relatório, o agente não entrega valor.

**Conclusão:** Este teste é o mais crítico porque valida o contrato principal da aplicação: "dado um repositório com documentação, produzir um relatório de análise completo e correto". Sua execução com sucesso garante que o caminho feliz funciona end-to-end.

### Cenário #4 — Prompt injection não altera comportamento

**Justificativa de priorização complementar:**

1. **Impacto no usuário: ALTO** — Vazamento de API keys ou manipulação de resultado compromete confiança e segurança.

2. **Probabilidade de falha: MÉDIA** — Documentos analisados são conteúdo não confiável. Atacantes podem injetar payloads deliberadamente.

3. **Severidade: CRÍTICA** — Exposição de credenciais ou manipulação de resultados é inaceitável.

## Decisão

Os testes E2E implementados em `tests/test_e2e.py` priorizam os cenários #1, #2, #3 e #9 (todos de risco ALTO ou MÉDIO com impacto direto no usuário). Os cenários de segurança (#4) são cobertos por `tests/test_prompt_injection.py`.

## Geração com Apoio de IA

Os testes E2E foram gerados e refinados com apoio de IA (Kiro/Claude), que:
- Identificou os cenários de maior risco com base na arquitetura
- Sugeriu assertions específicas para cada cenário
- Refiniu a cobertura para incluir validação de observabilidade
- Priorizou cenários que exercitam o fluxo completo (entrada → processamento → saída)
