# 📄 Doc Intelligence Agent

Um agente que avalia documentação técnica de software a partir de um repositório Git ou arquivos locais, identificando qualidade, lacunas e melhorias prioritárias em README e PRD.

## Funcionalidades

- **Análise multidimensional**: avalia clareza, cobertura, consistência e onboarding
- **Duas formas de entrada**: URL de repositório Git ou upload de arquivos Markdown
- **Relatório estruturado**: resumo, pontos fortes, problemas, checklist de melhorias, nota qualitativa e limitações
- **Descoberta automática**: localiza README.md, PRD.md e outros documentos por prioridade
- **Segurança**: sanitização de credenciais na saída (KEY, SECRET, TOKEN, PASSWORD)
- **Interface web**: Gradio com renderização Markdown

## Arquitetura

O agente utiliza **LangGraph** para orquestrar um grafo de 7 nós sequenciais com roteamento condicional:

```
receive_input → validate_input → discover_docs → read_docs → analyze_docs → build_report → present_result
```

Roteamento condicional encerra o fluxo antecipadamente em caso de:
- Validação inválida (URL malformada, caminho inexistente)
- Nenhum documento descoberto
- Contexto consolidado vazio

## Estrutura do Projeto

```
app/
├── main.py                          # Ponto de entrada
├── ui/
│   └── gradio_app.py                # Interface Gradio
├── agent/
│   ├── graph.py                     # Grafo LangGraph compilado
│   ├── state.py                     # AgentState (TypedDict, 13 campos)
│   └── nodes/
│       ├── receive_input.py         # Registra entrada e classifica tipo
│       ├── validate_input.py        # Valida URL/path/extensão
│       ├── discover_docs.py         # Clona repo e busca documentos
│       ├── read_docs.py             # Lê, normaliza e consolida
│       ├── analyze_docs.py          # Avalia 4 dimensões + nota
│       ├── build_report.py          # Gera relatório Markdown
│       └── present_result.py        # Nó terminal
├── tools/
│   ├── repo_tools.py                # validate_repository_url, clone_or_open_repository
│   ├── file_tools.py                # find_documentation_files, read_markdown_file
│   └── text_tools.py                # normalize_document_text
├── services/
│   ├── report_service.py            # generate_report_markdown
│   └── sanitizer.py                 # sanitize_text, sanitize_state
└── prompts/
    └── analysis_prompt.md           # Prompt de análise multidimensional
tests/
├── test_properties_repo.py          # PBT: validação URL e extensões
├── test_properties_files.py         # PBT: descoberta e normalização
├── test_properties_nodes_input.py   # PBT: receive_input, validate_input
├── test_properties_nodes_discover_read.py  # PBT: discover_docs, read_docs
├── test_properties_nodes_analyze_report.py # PBT: analyze, report
├── test_properties_sanitizer.py     # PBT: credenciais nunca expostas
├── test_graph.py                    # Integração do grafo completo
└── test_ui.py                       # Testes da interface Gradio
examples/
├── sample_readme.md                 # README de exemplo
├── sample_prd.md                    # PRD de exemplo
└── expected_report.md               # Relatório esperado
docs/
├── prompts.md                       # Prompts utilizados na sessão de spec
├── example_output.md                # Exemplo de relatório gerado
└── examples/
    ├── sample_readme.md             # README de exemplo (entrada)
    └── sample_prd.md                # PRD de exemplo (entrada)
```

## Requisitos

- Python 3.11+
- Dependências em `requirements.txt`

## Instalação

```bash
# Clonar repositório
git clone https://github.com/biel1993ph/doc-intelligence-agent.git
cd doc-intelligence-agent

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais
```

## Configuração

Edite o arquivo `.env`:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave de API do provedor LLM | — |
| `LLM_MODEL` | Modelo LLM para análise | — |
| `TEMP_CLONE_DIR` | Diretório para clonagem temporária | `/tmp/doc-intelligence-agent` |
| `LOG_LEVEL` | Nível de log | `INFO` |

## Uso

### Interface Web (Gradio)

```bash
python3 -m app.main
```

Acesse `http://localhost:7860` no navegador.

### Programático

```python
from app.agent.graph import run_agent

# Analisar repositório remoto
result = run_agent("https://github.com/user/repo")

# Analisar diretório local
result = run_agent("/caminho/para/projeto")

# Acessar relatório
print(result["final_report"])
```

## Exemplos de Entrada

O agente aceita repositórios completos contendo documentação técnica. Veja exemplos de documentos que podem ser analisados:

- [`docs/examples/sample_readme.md`](docs/examples/sample_readme.md) — README de um projeto Flutter com arquitetura, instalação e uso
- [`docs/examples/sample_prd.md`](docs/examples/sample_prd.md) — PRD completo com requisitos funcionais, regras de negócio e fluxos

Ao fornecer uma URL de repositório ou caminho local, o agente descobre automaticamente esses arquivos e os analisa em conjunto.

## Exemplo de Saída

Ao analisar um repositório, o agente gera um relatório estruturado em Markdown. Veja o exemplo completo em [`docs/example_output.md`](docs/example_output.md).

Trecho do relatório:

```markdown
# Relatório de Análise de Documentação

## Escopo
Arquivos analisados:
- README.md
- prd.md
- design.md

## Pontos Fortes
- ✅ Estrutura com cabeçalhos Markdown presente.
- ✅ Exemplos de código incluídos na documentação.
- ✅ Instruções de instalação disponíveis.

## Problemas Identificados
1. Guia de contribuição ausente.
   Recomendação: Adicionar CONTRIBUTING.md ou seção equivalente.

## Nota
10/10

| Dimensão | Avaliação |
|------------|-------------|
| Clareza | adequada |
| Cobertura | ampla |
| Consistência | consistente |
| Onboarding | presente |
```

## Testes

```bash
# Rodar todos os testes
python3 -m pytest tests/ -v

# Testes de propriedade (Hypothesis)
python3 -m pytest tests/test_properties_*.py -v

# Testes de integração do grafo
python3 -m pytest tests/test_graph.py -v

# Testes da interface
python3 -m pytest tests/test_ui.py -v
```

## Tech Stack

| Componente | Tecnologia |
|------------|------------|
| Orquestração | LangGraph (StateGraph) |
| Interface | Gradio |
| Clonagem Git | GitPython |
| HTTP | requests |
| Testes | pytest + Hypothesis (PBT) |
| Linguagem | Python 3.11+ |

## Limitações

- Análise baseada exclusivamente no conteúdo textual dos documentos Markdown
- Não avalia precisão técnica do conteúdo (apenas estrutura e completude)
- Timeout de 30s para validação de URL e 60s para clonagem
- Máximo de 5 documentos descobertos e 20 arquivos lidos por execução
- Arquivos limitados a 1 MB cada
