# Prompts Utilizados na Sessão de Spec

## 1. Prompt Inicial — Geração de Specs

```
Gerar as specs com base nos arquivos sterring.
```

## 2. Seleção de Tipo

Resposta: **Build a Feature**

## 3. Seleção de Workflow

Resposta: **Requirements** (Requirements-First)

## 4. Prompt para Geração de Requisitos

```
O usuário quer criar specs para o projeto "doc-intelligence-agent" (Build a Feature, Requirements-First).

Feature name: doc-intelligence-agent

Contexto do produto (steering files):

**Product:**
- Um agente que avalia documentação técnica de software a partir de um repositório Git ou arquivos locais, identificando qualidade, lacunas e melhorias prioritárias em README e PRD.
- Entradas: URL de repositório Git, arquivos README.md, PRD.md ou equivalentes em Markdown.
- Saída: Relatório estruturado com resumo, pontos fortes, problemas, checklist de melhorias, nota qualitativa e limitações.
- Fluxo: input → validação → descoberta de docs → leitura → análise → relatório → exibição no Gradio.

**Tech Stack:**
- Python 3.11+, LangGraph (orquestração), Gradio (UI), GitPython, pathlib.
- Estado LangGraph com campos: raw_input, input_type, validation_status, validation_message, repository_url, local_files, discovered_files, readme_content, prd_content, merged_context, analysis_result, final_report, errors.
- Nós: receive_input, validate_input, discover_docs, read_docs, analyze_docs, build_report, present_result.
- Ferramentas: validate_repository_url, clone_or_open_repository, find_documentation_files, read_markdown_file, normalize_document_text, generate_report_markdown.

**Estrutura do projeto:**
- app/ui, app/agent (graph, state, nodes/), app/tools, app/services, app/prompts
- docs/, examples/, tests/
- README.md, requirements.txt, .env.example, .gitignore

**Regras:**
- Validar antes de processar; falhar de forma segura.
- Não inventar requisitos ausentes.
- Sinalizar quando a base documental for insuficiente.
- Separar interface, agente, ferramentas, estado.
- Gerar saída estruturada e útil.

Gerar o requirements.md em português (pt-BR).
```

## 5. Prompt para Geração de Design

```
Create the design for doc-intelligence-agent
```

Prompt interno enviado ao subagente:

```
Generate the technical design document (design.md) for the feature "doc-intelligence-agent".

The requirements document is already complete at `.kiro/specs/doc-intelligence-agent/requirements.md`.

Key context from steering files:

**Tech Stack:**
- Python 3.11+
- LangGraph para orquestração do agente
- Gradio para interface web
- GitPython, pathlib e utilitários de filesystem
- Markdown parser/text processing

**Estrutura do projeto:**
- app/main.py (entrypoint)
- app/ui/gradio_app.py (interface)
- app/agent/graph.py, state.py, nodes/ (agente LangGraph)
- app/tools/repo_tools.py, file_tools.py, text_tools.py (ferramentas)
- app/services/report_service.py (geração de relatório)
- app/prompts/analysis_prompt.md (prompts)
- docs/, examples/, tests/

**Nós do grafo LangGraph:**
1. receive_input
2. validate_input
3. discover_docs
4. read_docs
5. analyze_docs
6. build_report
7. present_result

**Estado LangGraph (campos):**
raw_input, input_type, validation_status, validation_message, repository_url, local_files, discovered_files, readme_content, prd_content, merged_context, analysis_result, final_report, errors

**Ferramentas:**
- validate_repository_url (app/tools/repo_tools.py)
- clone_or_open_repository (app/tools/repo_tools.py)
- find_documentation_files (app/tools/file_tools.py)
- read_markdown_file (app/tools/file_tools.py)
- normalize_document_text (app/tools/text_tools.py)
- generate_report_markdown (app/services/report_service.py)

**Regras:**
- Separação clara: UI, agente, ferramentas, estado
- Dependência unidirecional: ui → agent → tools/services
- Sem dependências circulares
- Código modular, tipado, testável
- Validar antes de processar
- Falhar de forma segura e explicável

Gerar o design em português (pt-BR).
```

## 6. Prompt para Geração de Tarefas

```
Create the tasks for doc-intelligence-agent
```

Prompt interno enviado ao subagente:

```
Generate the tasks.md implementation task list for the feature "doc-intelligence-agent".

Both requirements.md and design.md are already complete at:
- `.kiro/specs/doc-intelligence-agent/requirements.md`
- `.kiro/specs/doc-intelligence-agent/design.md`

Key context:

**Tech Stack:** Python 3.11+, LangGraph, Gradio, GitPython, pathlib, hypothesis (PBT), pytest

**Project Structure:**
app/
├─ main.py
├─ ui/gradio_app.py
├─ agent/
│  ├─ graph.py
│  ├─ state.py
│  └─ nodes/ (receive_input, validate_input, discover_docs, read_docs, analyze_docs, build_report, present_result)
├─ tools/ (repo_tools.py, file_tools.py, text_tools.py)
├─ services/report_service.py
└─ prompts/analysis_prompt.md
tests/
examples/
docs/

**Design highlights:**
- 7 sequential LangGraph nodes with conditional routing on errors
- AgentState TypedDict with 13 fields
- 6 tool functions across 4 modules
- 13 correctness properties mapped to hypothesis-based PBT tests
- Error handling with categories: irrecoverable (end flow) vs recoverable (continue)
- Timeouts: URL validation 30s, clone 60s, UI total 120s

**Correctness Properties (from design):**
1. Registro correto de entrada no estado
2. Validação sintática de URL rejeita formatos inválidos
3. Validação de extensão aceita apenas .md/.markdown
4. Descoberta respeita prioridade e deduplicação
5. Normalização é idempotente
6. Contexto consolidado preserva conteúdo com rastreabilidade
7. Limites de leitura são respeitados
8. Resultado da análise respeita invariantes estruturais
9. Base insuficiente limita nota máxima
10. Relatório contém todas as seções na ordem correta
11. Isolamento de campos entre nós
12. Preservação de estado em erro
13. Credenciais nunca são expostas

Generate tasks in Portuguese (pt-BR).
```

## 7. Prompt para Criação de Issues no GitHub

```
Criar issues no GitHub Project a partir do tasks.md relacionando com requirements.md utilizando GitHub CLI.

Você é um agente técnico especializado em planejamento ágil, análise de requisitos e automação via GitHub CLI.

Sua função é:
1. Ler o conteúdo de tasks.md
2. Correlacionar cada tarefa com os requisitos descritos em requirements.md
3. Criar issues estruturadas no GitHub
4. Utilizar exclusivamente GitHub CLI (`gh`)

Objetivo: Transformar tarefas documentadas em issues rastreáveis, padronizadas e vinculadas ao contexto funcional definido nos requisitos do projeto.

Regras:
- Utilizar apenas GitHub CLI
- Criar uma issue por tarefa
- Relacionar cada issue com ao menos um requisito
- Manter títulos curtos e objetivos
- Gerar descrições técnicas claras
- Incluir critérios de aceite
- Adicionar labels apropriadas
- Evitar duplicidade de issues
- Não criar issues sem contexto funcional
- Utilizar markdown compatível com GitHub
- Manter padronização entre todas as issues

Estrutura da Issue:
- Title: Título curto e objetivo
- Body:
  ## Contexto — Descrição resumida da necessidade
  ## Requisito Relacionado — Referência ao requisito do requirements.md
  ## Objetivo — Resultado esperado da implementação
  ## Critérios de Aceite — Checklist com critérios
  ## Observações Técnicas — Detalhes importantes para implementação
```

## 8. Revisão — Consolidação de Issues

```
Revise a criação das tarefas pois não quero por exemplo 1.1 e 1.2,
Prefiro implementar todas subtask 1.1 e 1.2 tudo em uma única tarefa.
Para não ter grande quantidade tarefas muito pequenas.
```

Resultado: Issues consolidadas de ~30 subtarefas individuais para 11 issues agrupadas por tarefa principal:

| # | Issue | Labels |
|---|-------|--------|
| 15 | Configurar estrutura do projeto e dependências | setup |
| 16 | Implementar ferramentas de repositório e validação | tools |
| 17 | Implementar ferramentas de arquivo e texto | tools |
| 18 | Implementar nós do grafo: entrada e validação | agent |
| 19 | Implementar nós do grafo: descoberta e leitura | agent |
| 20 | Implementar nós do grafo: análise e relatório | agent |
| 21 | Montar e compilar o grafo LangGraph | agent |
| 22 | Implementar filtragem de credenciais e segurança | security |
| 23 | Implementar interface Gradio e ponto de entrada | ui |
| 24 | Criar prompt de análise e arquivos de exemplo | documentation |
| 25 | Testes de integração, fumaça e infraestrutura | testing |

Labels criadas: `setup`, `ui`, `testing`, `security`, `agent`, `tools`


## 9. Prompt para Execução de Issues (GitFlow)

Prompt padrão utilizado para executar cada issue individualmente:

```
Você é um desenvolvedor responsável por executar exatamente o que está descrito na issue do GitHub abaixo, utilizando GitHub CLI e seguindo fluxo GitFlow.

Link da issue: https://github.com/biel1993ph/doc-intelligence-agent/issues/<N>
Link do Repositório: https://github.com/biel1993ph/doc-intelligence-agent

Seu trabalho é:
1. Ler completamente a issue.
2. Colocar a issue em In Progress.
3. Criar uma branch baseada na develop.
4. Implementar exclusivamente o que está descrito na issue.
5. Não criar documentação desnecessária.
6. Não alterar escopo além do solicitado.
7. Realizar commits objetivos e coerentes com a implementação.

Regras:
- Branch base: develop
- Nome da branch: feature/issue-<N>-<descricao-curta>
- Executar somente o que estiver explícito na issue.
- Manter consistência com arquitetura atual do projeto.
- Criar commits pequenos e objetivos.
- Utilizar GitHub CLI sempre que possível.

Proibido:
- Não criar README extra.
- Não criar documentação técnica adicional.
- Não refatorar partes não relacionadas.
- Não alterar dependências sem necessidade.
- Não implementar melhorias "aproveitando a oportunidade".

Fluxo:
1. git checkout develop && git pull origin develop
2. gh issue view <N> --repo biel1993ph/doc-intelligence-agent
3. gh issue edit <N> --add-label "in progress"
4. git checkout -b feature/issue-<N>-<descricao-curta>
5. Implementar
6. Rodar testes relevantes
7. git add <arquivos> && git commit -m "feat: <descrição> (#<N>)"
8. git push -u origin feature/issue-<N>-<descricao-curta>
9. gh pr create --base develop --title "feat: <titulo> (#<N>)" --body "Closes #<N>"
10. gh pr merge <PR> --squash
11. gh issue close <N> --reason completed
```

## 10. Issues Executadas — Resumo

| Issue | Branch | PR | Status |
|-------|--------|-----|--------|
| #16 | feature/issue-16-repo-tools | #28 | ✅ Merged + Closed |
| #17 | feature/issue-17-file-text-tools | #29 | ✅ Merged + Closed |
| #18 | feature/issue-18-nodes-input-validation | #30 | ✅ Merged + Closed |
| #19 | feature/issue-19-nodes-discover-read | #31 | ✅ Merged + Closed |
| #20 | feature/issue-20-nodes-analyze-report | #32 | ✅ Merged + Closed |
| #21 | feature/issue-21-compile-graph | #33 | ✅ Merged + Closed |
| #22 | feature/issue-22-credential-filter | #34 | ✅ Merged + Closed |
| #23 | feature/issue-23-gradio-ui | #35 | ✅ Merged + Closed |
| #24 | feature/issue-24-prompts-examples | #36 | ✅ Merged + Closed |
| #25 | — | — | ⏳ Pendente |

## 11. Prompt para Merge e Finalização de Issue

```
Realizar o merge do Pull Request #<PR> no repositório doc-intelligence-agent
utilizando exclusivamente GitHub CLI (gh) e atualizar o status da tarefa
relacionada para DONE.

Fluxo:
1. gh pr view <PR> --repo biel1993ph/doc-intelligence-agent --json state,mergeable,baseRefName
2. gh pr checks <PR> --repo biel1993ph/doc-intelligence-agent
3. gh pr view <PR> --repo biel1993ph/doc-intelligence-agent --json reviews
4. gh pr merge <PR> --repo biel1993ph/doc-intelligence-agent --squash
5. gh issue close <N> --repo biel1993ph/doc-intelligence-agent --reason completed

Regras:
- NÃO deletar a branch após o merge
- Preferir squash merge
- Verificar que não há checks pendentes ou conflitos
- Fechar issue como completed via GitHub CLI
```

## 12. Correção de Erro de Execução — ModuleNotFoundError

**Problema:** Ao executar `python3 app/main.py`, ocorria:
```
ModuleNotFoundError: No module named 'app'
```

**Causa:** O `main.py` usa imports absolutos (`from app.ui.gradio_app import create_app`), mas executar como `python3 app/main.py` coloca o diretório `app/` no `sys.path` ao invés da raiz do projeto.

**Solução aplicada:**
- Atualizar README.md para instruir execução via `python3 -m app.main`

```
Estou com erro na imagem em anexo ao executar Interface Web.
ModuleNotFoundError: No module named 'app'
```

## 13. Ajuste da Interface — Repositório Local e Upload Múltiplo

**Problema:** A interface Gradio não permitia:
1. Informar caminho de repositório local (só aceitava URL remota)
2. Anexar mais de um arquivo por vez (README + PRD)

**Solução aplicada:**
- Adicionado campo "Caminho do Repositório Local" na interface
- Mantido `file_count="multiple"` com label mais claro
- Atualizada `handle_submission` para aceitar 3 modos mutuamente exclusivos: URL, caminho local ou upload de arquivos
- Atualizados testes em `tests/test_ui.py` (9 testes, todos passando)

```
Realizar ajustes para anexar o repositório local ou anexar mais de um (Readme e um PRD).
Atualmente não é permitido anexar mais de um arquivo. Como também não é possível anexar um repositório local.
```

**Arquivos modificados:**
- `app/ui/gradio_app.py` — nova assinatura `handle_submission(url, local_path, files)` + novo campo Gradio
- `tests/test_ui.py` — testes atualizados para nova assinatura (9 testes)
- `README.md` — comando de execução corrigido para `python3 -m app.main`

## 14. Erro de Porta Ocupada — OSError: Address Already in Use

**Problema:** Ao parar o servidor com `Ctrl+Z` e reiniciar, ocorria:
```
OSError: Cannot find empty port in range: 7860-7860.
[Errno 48] address already in use
```

**Causa:** `Ctrl+Z` apenas **suspende** o processo (fica em background segurando a porta), não o encerra. O processo suspenso ainda ocupa a porta 7860.

**Solução:**
1. Matar o processo suspenso: `kill %1`
2. Ou forçar liberação da porta: `lsof -ti :7860 | xargs kill -9`
3. Usar `Ctrl+C` (em vez de `Ctrl+Z`) para encerrar o servidor corretamente

```
Estou com esse erro, parei o serviço e subi novamente.
OSError: Cannot find empty port in range: 7860-7860. address already in use.
```
