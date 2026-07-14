# Tech Steering — Document Analysis Agent

## Stack principal
- Python 3.11+
- LangGraph para orquestração do agente
- Gradio para interface web
- GitPython, pathlib e utilitários de filesystem para leitura de repositório local/remoto
- Markdown parser/text processing para leitura e segmentação de README e PRD

## Objetivo técnico
Construir um agente funcional que receba um repositório Git ou arquivos locais, processe a documentação e gere um relatório estruturado com diagnóstico e recomendações.

## Diretrizes técnicas
- Usar LangGraph como núcleo do fluxo.
- Cada etapa principal do agente deve ser representada por um nó do grafo.
- O estado compartilhado deve armazenar entrada, status de validação, caminhos dos arquivos encontrados, conteúdos lidos, análise e relatório final.
- A solução deve ter pelo menos uma ferramenta real integrada ao fluxo, como leitura de arquivos locais ou clonagem/inspeção de repositório.
- A interface Gradio deve permitir dois modos de entrada:
  - URL do repositório
  - Upload de arquivos README/PRD
- O projeto deve separar claramente:
  - interface
  - fluxo do agente
  - ferramentas
  - schemas/estado
  - geração de relatório

## Regras de implementação
- Validar entrada antes de qualquer leitura.
- Não processar entradas vazias, URLs malformadas ou arquivos não suportados.
- Priorizar arquivos:
  1. README.md
  2. PRD.md
  3. arquivos equivalentes como docs/README.md, product_requirements.md, docs/prd.md
- O agente deve falhar de forma segura e explicável.
- Toda saída do agente deve ser determinística o suficiente para avaliação acadêmica.
- Nunca expor segredos em logs ou respostas.
- Preparar `.env.example` se houver dependências externas.
- Adicionar `.gitignore` para arquivos sensíveis e temporários.

## Estado sugerido do LangGraph
Campos mínimos:
- raw_input
- input_type
- validation_status
- validation_message
- repository_url
- local_files
- discovered_files
- readme_content
- prd_content
- merged_context
- analysis_result
- final_report
- errors

## Nós sugeridos
1. receive_input
2. validate_input
3. discover_docs
4. read_docs
5. analyze_docs
6. build_report
7. present_result

## Ferramentas sugeridas
- `validate_repository_url`
- `clone_or_open_repository`
- `find_documentation_files`
- `read_markdown_file`
- `normalize_document_text`
- `generate_report_markdown`

## Qualidade esperada
- Código modular
- Funções pequenas e testáveis
- Tipagem sempre que possível
- Mensagens de erro claras
- Exemplo real de entrada e saída no README
- Prompts versionados em `docs/prompts.md`

## Restrições
- Não acoplar lógica de interface com lógica do agente.
- Não concentrar todo o fluxo em um único arquivo.
- Não usar ferramentas fictícias.
- Não deixar validações implícitas.