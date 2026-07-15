# Implementation Plan: Agente de Análise de Documentação de Software

## Overview

Implementação incremental do agente LangGraph com 7 nós sequenciais, ferramentas desacopladas, serviço de relatório e interface Gradio. Cada tarefa constrói sobre a anterior, integrando componentes progressivamente até o fluxo completo.

## Tasks

- [ ] 1. Configurar estrutura do projeto e dependências
  - [ ] 1.1 Criar estrutura de diretórios e arquivos base
    - Criar diretórios: `app/`, `app/ui/`, `app/agent/`, `app/agent/nodes/`, `app/tools/`, `app/services/`, `app/prompts/`, `tests/`, `examples/`, `docs/`
    - Criar arquivos `__init__.py` em cada módulo Python
    - Criar `requirements.txt` com dependências: langgraph, gradio, gitpython, hypothesis, pytest, pytest-cov
    - Criar `.env.example` com variáveis documentadas
    - Criar `.gitignore` para arquivos temporários, `.env`, `__pycache__`, `.pytest_cache`
    - _Requisitos: 9.1, 9.9, 9.10, 10.4_

  - [ ] 1.2 Definir o estado tipado do agente (`app/agent/state.py`)
    - Implementar `ErrorEntry` como `TypedDict` com campos `node: str` e `message: str`
    - Implementar `AgentState` como `TypedDict` com os 13 campos definidos no design
    - Incluir valores padrão documentados em comentários
    - _Requisitos: 8.1, 8.3_

- [ ] 2. Implementar ferramentas de repositório e validação
  - [ ] 2.1 Implementar `validate_repository_url` em `app/tools/repo_tools.py`
    - Validar esquema (http/https), host válido e formato de URL
    - Verificar acessibilidade com timeout de 30 segundos
    - Retornar tupla `(bool, str)` com resultado e mensagem
    - _Requisitos: 2.1, 2.4, 2.5, 9.3, 10.1_

  - [ ] 2.2 Implementar `clone_or_open_repository` em `app/tools/repo_tools.py`
    - Clonar repositório remoto usando GitPython com timeout de 60 segundos
    - Usar `tempfile.TemporaryDirectory` para diretório de clonagem
    - Tratar erros de rede/autenticação e timeout com mensagens claras
    - Limpar diretório temporário em caso de falha (bloco finally)
    - _Requisitos: 3.1, 3.6, 10.5, 10.6_

  - [ ]* 2.3 Escrever teste de propriedade para validação de URL
    - **Propriedade 2: Validação sintática de URL rejeita formatos inválidos**
    - **Valida: Requisitos 2.1, 2.4**

  - [ ]* 2.4 Escrever teste de propriedade para validação de extensão de arquivo
    - **Propriedade 3: Validação de extensão aceita apenas .md e .markdown**
    - **Valida: Requisitos 2.2, 2.6, 2.7**

- [ ] 3. Implementar ferramentas de arquivo e texto
  - [ ] 3.1 Implementar `find_documentation_files` em `app/tools/file_tools.py`
    - Definir `PRIORITY_PATTERNS` com ordem de prioridade do design
    - Buscar arquivos Markdown seguindo prioridade, máximo 5 resultados
    - Implementar deduplicação case-insensitive (manter primeira ocorrência)
    - _Requisitos: 3.1, 3.3, 3.5, 9.5_

  - [ ] 3.2 Implementar `read_markdown_file` em `app/tools/file_tools.py`
    - Ler arquivo com limite de 1 MB
    - Implementar fallback de encoding UTF-8 → Latin-1
    - Retornar tupla `(content | None, error | None)`
    - _Requisitos: 4.1, 4.5, 4.7, 9.6_

  - [ ] 3.3 Implementar `normalize_document_text` em `app/tools/text_tools.py`
    - Remover linhas em branco consecutivas (manter no máximo uma)
    - Trim de espaços em início/fim de cada linha
    - Garantir codificação UTF-8
    - _Requisitos: 4.2, 4.3, 9.7_

  - [ ]* 3.4 Escrever teste de propriedade para descoberta com prioridade
    - **Propriedade 4: Descoberta de documentos respeita ordem de prioridade e deduplicação**
    - **Valida: Requisitos 3.1, 3.3, 3.5**

  - [ ]* 3.5 Escrever teste de propriedade para normalização idempotente
    - **Propriedade 5: Normalização de texto é idempotente**
    - **Valida: Requisitos 4.2, 4.3**

- [ ] 4. Checkpoint — Verificar ferramentas isoladas
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 5. Implementar nós do grafo (parte 1: entrada e validação)
  - [ ] 5.1 Implementar nó `receive_input` em `app/agent/nodes/receive_input.py`
    - Registrar `raw_input` e `input_type` no estado
    - Não alterar nenhum outro campo do estado
    - _Requisitos: 1.2, 1.3, 8.2_

  - [ ] 5.2 Implementar nó `validate_input` em `app/agent/nodes/validate_input.py`
    - Validar entrada conforme tipo (URL ou arquivos)
    - Usar `validate_repository_url` para URLs
    - Verificar extensões `.md`/`.markdown` para arquivos
    - Registrar `validation_status`, `validation_message`, `repository_url`, `local_files`
    - Tratar entrada vazia e ambos os campos preenchidos
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 8.2_

  - [ ]* 5.3 Escrever teste de propriedade para registro de entrada
    - **Propriedade 1: Registro correto de entrada no estado**
    - **Valida: Requisitos 1.2, 1.3**

- [ ] 6. Implementar nós do grafo (parte 2: descoberta e leitura)
  - [ ] 6.1 Implementar nó `discover_docs` em `app/agent/nodes/discover_docs.py`
    - Para `input_type == "repository"`: clonar repositório e usar `find_documentation_files`
    - Para `input_type == "local_files"`: verificar existência e extensão dos caminhos
    - Registrar `discovered_files` no estado
    - Tratar caso de nenhum documento encontrado (adicionar erro e sinalizar fim)
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.2_

  - [ ] 6.2 Implementar nó `read_docs` em `app/agent/nodes/read_docs.py`
    - Ler cada arquivo de `discovered_files` usando `read_markdown_file`
    - Normalizar conteúdo com `normalize_document_text`
    - Identificar e armazenar `readme_content` e `prd_content`
    - Consolidar em `merged_context` com cabeçalhos de rastreabilidade
    - Respeitar limite de 20 arquivos e 1 MB por arquivo
    - Tratar caso de `merged_context` vazio (adicionar erro e sinalizar fim)
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 8.2_

  - [ ]* 6.3 Escrever teste de propriedade para contexto consolidado
    - **Propriedade 6: Contexto consolidado preserva todo conteúdo com rastreabilidade**
    - **Valida: Requisitos 4.4**

  - [ ]* 6.4 Escrever teste de propriedade para limites de leitura
    - **Propriedade 7: Limites de leitura são respeitados**
    - **Valida: Requisitos 4.1, 4.5**

- [ ] 7. Implementar nós do grafo (parte 3: análise e relatório)
  - [ ] 7.1 Implementar nó `analyze_docs` em `app/agent/nodes/analyze_docs.py`
    - Avaliar `merged_context` nas 4 dimensões: clareza, cobertura, consistência, onboarding
    - Identificar pontos fortes (1-10 itens, cada um ≤ 280 chars)
    - Identificar problemas (1-15 itens, classificados como "observacao" ou "recomendacao")
    - Gerar nota qualitativa (0-10) com justificativa (≥ 2 frases)
    - Tratar base insuficiente (< 100 chars): `base_insuficiente = True`, nota máx. 3
    - Marcar dimensões não avaliáveis quando não houver conteúdo correspondente
    - Registrar `analysis_result` no estado
    - Usar prompt de `app/prompts/analysis_prompt.md`
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 8.2_

  - [ ] 7.2 Implementar serviço `generate_report_markdown` em `app/services/report_service.py`
    - Gerar relatório Markdown com 7 seções na ordem correta (headings `##`)
    - Incluir nota numérica com justificativa
    - Incluir caminhos relativos dos arquivos analisados
    - Incluir todas as limitações registradas
    - Cada seção com contexto suficiente para leitura independente
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.6, 9.8_

  - [ ] 7.3 Implementar nó `build_report` em `app/agent/nodes/build_report.py`
    - Invocar `generate_report_markdown` com `analysis_result` e `discovered_files`
    - Registrar `final_report` no estado
    - Tratar caso de `analysis_result` ausente/incompleto (gerar relatório parcial)
    - _Requisitos: 6.1, 6.5, 6.7, 8.2_

  - [ ] 7.4 Implementar nó `present_result` em `app/agent/nodes/present_result.py`
    - Nó terminal que sinaliza conclusão do fluxo
    - Não altera nenhum campo do estado
    - _Requisitos: 7.1, 8.2_

  - [ ]* 7.5 Escrever teste de propriedade para estrutura do resultado de análise
    - **Propriedade 8: Resultado da análise respeita invariantes estruturais**
    - **Valida: Requisitos 5.2, 5.3, 5.4, 5.5**

  - [ ]* 7.6 Escrever teste de propriedade para base insuficiente
    - **Propriedade 9: Base insuficiente limita nota máxima**
    - **Valida: Requisitos 5.6**

  - [ ]* 7.7 Escrever teste de propriedade para estrutura do relatório
    - **Propriedade 10: Relatório contém todas as seções na ordem correta**
    - **Valida: Requisitos 6.1, 6.2, 6.3, 6.4**

- [ ] 8. Checkpoint — Verificar nós isolados
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 9. Montar e compilar o grafo LangGraph
  - [ ] 9.1 Implementar `build_graph` e `run_agent` em `app/agent/graph.py`
    - Criar `StateGraph` com `AgentState`
    - Adicionar os 7 nós na sequência correta
    - Implementar roteamento condicional:
      - Após `validate_input`: se `validation_status == "invalid"` → END
      - Após `discover_docs`: se `discovered_files` vazio → END
      - Após `read_docs`: se `merged_context` vazio → END
    - Compilar o grafo com `graph.compile()`
    - Implementar `run_agent(raw_input, input_type)` que executa o grafo e retorna estado final
    - _Requisitos: 8.2, 8.4, 8.5, 9.1, 9.9_

  - [ ]* 9.2 Escrever teste de propriedade para isolamento de campos
    - **Propriedade 11: Isolamento de campos entre nós**
    - **Valida: Requisitos 8.2**

  - [ ]* 9.3 Escrever teste de propriedade para preservação de estado em erro
    - **Propriedade 12: Preservação de estado em caso de erro**
    - **Valida: Requisitos 8.4, 8.5**

- [ ] 10. Implementar filtragem de credenciais e segurança
  - [ ] 10.1 Implementar filtragem de credenciais no fluxo
    - Garantir que valores de variáveis contendo `KEY`, `SECRET`, `TOKEN`, `PASSWORD` não apareçam em `final_report` nem em `errors`
    - Implementar função utilitária de sanitização aplicada antes da saída
    - _Requisitos: 10.3_

  - [ ]* 10.2 Escrever teste de propriedade para filtragem de credenciais
    - **Propriedade 13: Credenciais nunca são expostas na saída**
    - **Valida: Requisitos 10.3**

- [ ] 11. Implementar interface Gradio
  - [ ] 11.1 Implementar `create_app` e `handle_submission` em `app/ui/gradio_app.py`
    - Criar interface com dois modos de entrada mutuamente exclusivos (URL ou upload)
    - Implementar callback `handle_submission` que invoca `run_agent`
    - Validar exclusividade de modo (não permitir ambos preenchidos)
    - Exibir indicador de carregamento durante processamento
    - Renderizar relatório Markdown na área de resultado
    - Exibir mensagens de erro quando fluxo interrompido
    - Implementar timeout de 120 segundos na UI
    - _Requisitos: 1.1, 1.4, 1.5, 1.6, 7.1, 7.2, 7.3, 7.4, 7.5, 9.2_

  - [ ] 11.2 Implementar `app/main.py` como ponto de entrada
    - Importar e inicializar a aplicação Gradio
    - Configurar servidor para execução local
    - _Requisitos: 9.1, 9.9_

- [ ] 12. Criar prompt de análise e exemplos
  - [ ] 12.1 Criar `app/prompts/analysis_prompt.md`
    - Definir prompt estruturado para análise multidimensional
    - Incluir instruções para as 4 dimensões de avaliação
    - Incluir formato esperado de saída (JSON compatível com `analysis_result`)
    - Incluir regras para nota qualitativa e tratamento de base insuficiente
    - _Requisitos: 5.1, 5.4, 5.6_

  - [ ] 12.2 Criar arquivos de exemplo em `examples/`
    - Criar `examples/sample_readme.md` com README de exemplo
    - Criar `examples/sample_prd.md` com PRD de exemplo
    - Criar `examples/expected_report.md` com relatório esperado de exemplo
    - _Requisitos: (suporte a demonstração e testes)_

- [ ] 13. Testes de integração e fumaça
  - [ ]* 13.1 Escrever testes de integração em `tests/test_integration.py`
    - Testar fluxo completo com repositório local contendo README.md
    - Testar fluxo com upload de arquivos .md válidos
    - Testar fluxo interrompido por validação inválida
    - Testar timeout de clonagem simulado
    - _Requisitos: 8.4, 8.5, 10.2, 10.5_

  - [ ]* 13.2 Escrever testes de fumaça em `tests/test_smoke.py`
    - Verificar importação isolada de cada módulo
    - Verificar que `AgentState` contém todos os campos com tipos corretos
    - Verificar ausência de dependências circulares
    - Verificar que `.env.example` existe
    - _Requisitos: 9.9, 9.10, 10.4_

  - [ ]* 13.3 Criar `tests/conftest.py` com fixtures compartilhadas
    - Configurar perfis do Hypothesis (dev: 100 examples, ci: 200 examples)
    - Criar fixtures para estados de agente pré-populados
    - Criar generators reutilizáveis para URLs, listas de arquivos, árvores de diretório
    - _Requisitos: (infraestrutura de teste)_

- [ ] 14. Checkpoint final — Validação completa
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam exemplos específicos e edge cases
- A linguagem de implementação é Python 3.11+ conforme definido no design

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1", "2.2", "3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["2.3", "2.4", "3.4", "3.5"] },
    { "id": 4, "tasks": ["5.1", "5.2"] },
    { "id": 5, "tasks": ["5.3", "6.1", "6.2"] },
    { "id": 6, "tasks": ["6.3", "6.4", "7.1", "7.2"] },
    { "id": 7, "tasks": ["7.3", "7.4", "7.5", "7.6", "7.7"] },
    { "id": 8, "tasks": ["9.1"] },
    { "id": 9, "tasks": ["9.2", "9.3", "10.1"] },
    { "id": 10, "tasks": ["10.2", "11.1", "11.2", "12.1", "12.2"] },
    { "id": 11, "tasks": ["13.1", "13.2", "13.3"] }
  ]
}
```
