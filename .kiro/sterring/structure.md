# Structure Steering — Document Analysis Agent

## Objetivo
Padronizar a organização do repositório para facilitar desenvolvimento, manutenção, apresentação e avaliação.

## Estrutura sugerida

```text
project-root/
├─ app/
│  ├─ main.py
│  ├─ ui/
│  │  └─ gradio_app.py
│  ├─ agent/
│  │  ├─ graph.py
│  │  ├─ state.py
│  │  ├─ nodes/
│  │  │  ├─ receive_input.py
│  │  │  ├─ validate_input.py
│  │  │  ├─ discover_docs.py
│  │  │  ├─ read_docs.py
│  │  │  ├─ analyze_docs.py
│  │  │  ├─ build_report.py
│  │  │  └─ present_result.py
│  ├─ tools/
│  │  ├─ repo_tools.py
│  │  ├─ file_tools.py
│  │  └─ text_tools.py
│  ├─ services/
│  │  └─ report_service.py
│  └─ prompts/
│     └─ analysis_prompt.md
├─ docs/
│  ├─ prompts.md
│  ├─ tech.md
│  ├─ structure.md
│  └─ product.md
├─ examples/
│  ├─ sample_readme.md
│  ├─ sample_prd.md
│  └─ expected_report.md
├─ tests/
│  ├─ test_validation.py
│  ├─ test_discovery.py
│  └─ test_report.py
├─ README.md
├─ requirements.txt
├─ .env.example
└─ .gitignore
```

## Regras de organização
- `app/ui` contém somente interface.
- `app/agent` contém fluxo, estado e nós do LangGraph.
- `app/tools` contém integrações e funções utilitárias acionadas pelo agente.
- `app/services` concentra montagem de relatórios e regras reaproveitáveis.
- `docs` contém documentação do projeto e steering files.
- `examples` contém casos de teste manual e exemplos para apresentação.
- `tests` cobre validação, descoberta de arquivos e geração de relatório.

## Convenções
- Um arquivo por responsabilidade principal.
- Nomes de arquivos em snake_case.
- Nós do LangGraph devem ter nomes equivalentes às etapas do fluxo.
- Prompts ficam versionados e separados do código procedural.
- O README deve refletir a estrutura real do projeto.

## Fluxo lógico
- Entrada do usuário
- Validação
- Descoberta de documentação
- Leitura dos arquivos
- Consolidação de contexto
- Análise
- Geração do relatório
- Exibição final

## Saídas esperadas
- Relatório renderizado na interface Gradio
- Possibilidade de exibir o relatório em Markdown
- Exemplos salvos para demonstração acadêmica

## Restrições estruturais
- Não misturar exemplos com código de produção.
- Não colocar prompts soltos fora de `docs` ou `app/prompts`.
- Não criar dependência circular entre nós e ferramentas.
- Não deixar arquivos críticos fora da raiz do projeto, como README.md e requirements.txt.