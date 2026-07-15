# Requirements Document

## Introduction

O **Agente de Análise de Documentação de Software** é um sistema que automatiza a avaliação da qualidade de documentação técnica de projetos de software. A partir de um repositório Git (via URL) ou de arquivos locais enviados pelo usuário, o agente localiza, lê e analisa arquivos README e PRD, gerando um relatório estruturado com resumo executivo, pontos fortes, problemas encontrados, checklist de melhorias, nota qualitativa e limitações da análise. O fluxo é orquestrado por LangGraph e exposto ao usuário via interface Gradio.

---

## Glossary

- **Agente**: O sistema LangGraph que orquestra todo o fluxo de análise de documentação.
- **Grafo**: O grafo LangGraph composto pelos nós que executam o fluxo do Agente.
- **Estado**: Objeto compartilhado entre os nós do Grafo que armazena entradas, resultados intermediários e a saída final.
- **Nó**: Unidade de processamento dentro do Grafo responsável por uma etapa específica do fluxo.
- **Ferramenta**: Função utilitária invocada por um Nó para executar uma operação concreta (ex.: clonar repositório, ler arquivo).
- **Repositório**: Repositório Git acessível por URL pública ou presente localmente no sistema de arquivos.
- **Documento**: Arquivo de texto em formato Markdown que descreve aspectos do software (ex.: README.md, PRD.md).
- **README**: Arquivo de documentação principal do projeto, tipicamente `README.md` ou equivalente.
- **PRD**: Arquivo de requisitos de produto, tipicamente `PRD.md`, `product_requirements.md` ou equivalente.
- **Contexto_Consolidado**: Conteúdo textual resultante da combinação dos Documentos lidos, usado como entrada para a análise.
- **Relatório**: Saída estruturada em Markdown gerada pelo Agente após a análise.
- **Interface**: Componente Gradio que expõe o Agente ao usuário final.
- **Validador**: Componente responsável por verificar a validade das entradas antes do processamento.
- **Descobridor**: Componente responsável por localizar Documentos relevantes dentro de um Repositório.
- **Leitor**: Componente responsável por ler o conteúdo dos Documentos descobertos.
- **Analisador**: Componente responsável por avaliar o Contexto_Consolidado e produzir o resultado da análise.
- **Construtor_Relatorio**: Componente responsável por formatar o resultado da análise em um Relatório estruturado.

---

## Requirements

### Requirement 1: Recebimento de Entrada

**User Story:** Como usuário, quero informar uma URL de repositório Git ou enviar arquivos de documentação, para que o Agente possa iniciar a análise.

#### Acceptance Criteria

1. WHEN a Interface é carregada, THE Interface SHALL exibir dois modos de entrada mutuamente exclusivos: um campo de texto para URL de repositório Git e um campo de upload para arquivos com extensão `.md`.
2. WHEN o usuário submete uma URL de repositório Git, THE Agente SHALL registrar a URL no Estado como `repository_url` e definir `input_type` como `"repository"`.
3. WHEN o usuário envia um ou mais arquivos via upload (máximo de 10 arquivos, cada um com extensão `.md`), THE Agente SHALL registrar os caminhos dos arquivos no Estado como `local_files` e definir `input_type` como `"local_files"`.
4. WHEN o usuário submete a entrada com dados válidos, THE Interface SHALL iniciar o processamento e exibir um indicador de que a análise está em andamento.
5. IF o usuário submete a entrada sem preencher nenhum dos campos (URL vazia e nenhum arquivo selecionado), THEN THE Interface SHALL exibir uma mensagem de erro indicando que é necessário fornecer uma URL ou pelo menos um arquivo para iniciar a análise.
6. IF o usuário tenta submeter com ambos os campos preenchidos (URL e arquivos simultaneamente), THEN THE Interface SHALL exibir uma mensagem de erro indicando que apenas um modo de entrada deve ser utilizado por vez.

---

### Requirement 2: Validação de Entrada

**User Story:** Como usuário, quero que o sistema valide minha entrada antes de processá-la, para que eu receba uma mensagem clara caso forneça dados inválidos.

#### Acceptance Criteria

1. WHEN a entrada recebida for uma URL, THE Validador SHALL verificar se a URL está sintaticamente bem-formada (esquema http/https, host válido) e acessível (resposta de rede dentro de 30 segundos) antes de prosseguir.
2. WHEN a entrada recebida for uma lista de arquivos, THE Validador SHALL verificar se cada arquivo possui extensão `.md` ou `.markdown` antes de prosseguir.
3. WHEN a entrada estiver vazia, THE Validador SHALL registrar `validation_status` como `"invalid"` e `validation_message` com a mensagem `"Nenhuma entrada fornecida. Informe uma URL ou envie arquivos."` e interromper o fluxo.
4. IF a URL fornecida for sintaticamente malformada, THEN THE Validador SHALL registrar `validation_status` como `"invalid"` e `validation_message` com descrição do problema e interromper o fluxo.
5. IF a URL for sintaticamente válida porém inacessível (timeout de 30 segundos ou código de erro HTTP), THEN THE Validador SHALL registrar `validation_status` como `"invalid"` e `validation_message` indicando que o repositório não está acessível e interromper o fluxo.
6. IF nenhum dos arquivos enviados possuir extensão suportada, THEN THE Validador SHALL registrar `validation_status` como `"invalid"` e `validation_message` com a mensagem `"Nenhum arquivo Markdown válido encontrado na entrada."` e interromper o fluxo.
7. WHEN a validação for bem-sucedida, THE Validador SHALL registrar `validation_status` como `"valid"` e prosseguir para a descoberta de documentos.

---

### Requirement 3: Descoberta de Documentos

**User Story:** Como usuário, quero que o sistema localize automaticamente os arquivos de documentação relevantes, para que eu não precise indicar manualmente cada arquivo.

#### Acceptance Criteria

1. WHEN o `input_type` for `"repository"`, THE Descobridor SHALL clonar o repositório remoto (ou abrir o diretório local caso já exista) e buscar Documentos na árvore de arquivos seguindo a ordem de prioridade: `README.md`, `PRD.md`, `docs/README.md`, `product_requirements.md`, `docs/prd.md`, selecionando no máximo 5 arquivos correspondentes.
2. WHEN o `input_type` for `"local_files"`, THE Descobridor SHALL verificar a existência de cada caminho em `local_files` e registrar como Documentos descobertos apenas os arquivos que existem e possuem extensão `.md`.
3. WHEN a etapa de descoberta concluir com ao menos um Documento encontrado, THE Descobridor SHALL registrar no Estado, no campo `discovered_files`, a lista de caminhos absolutos dos Documentos encontrados.
4. IF nenhum Documento for encontrado após a busca, THEN THE Descobridor SHALL registrar o evento no campo `errors` e interromper o fluxo com mensagem indicando que nenhum arquivo de documentação foi encontrado no repositório.
5. IF o Repositório contiver múltiplos arquivos candidatos com o mesmo nome de arquivo (case-insensitive) em diretórios diferentes, THEN THE Descobridor SHALL selecionar apenas a primeira ocorrência conforme a ordem de prioridade definida no critério 1 e descartar as demais.
6. IF a operação de clonagem do repositório falhar por erro de rede ou autenticação, THEN THE Descobridor SHALL registrar o erro no campo `errors` com mensagem indicando falha na clonagem e interromper o fluxo sem prosseguir para a busca de arquivos.
7. IF algum caminho em `local_files` não existir ou não for um arquivo válido, THEN THE Descobridor SHALL ignorar o caminho inválido e continuar o processamento com os arquivos restantes.

---

### Requirement 4: Leitura de Documentos

**User Story:** Como desenvolvedor, quero que o sistema leia o conteúdo dos documentos descobertos, para que o agente tenha base textual suficiente para a análise.

#### Acceptance Criteria

1. WHEN os Documentos forem descobertos com sucesso, THE Leitor SHALL ler o conteúdo de cada arquivo listado em `discovered_files`, limitando-se a arquivos de no máximo 1 MB de tamanho e processando no máximo 20 arquivos por execução.
2. WHEN o arquivo lido possuir nome que corresponda ao padrão README (ex: `README.md`, `readme.md`, `docs/README.md`), THE Leitor SHALL armazenar seu conteúdo normalizado no Estado como `readme_content`, onde normalização consiste em remoção de linhas em branco consecutivas (manter no máximo uma), trim de espaços em início/fim de linha e conversão para codificação UTF-8.
3. WHEN o arquivo lido possuir nome que corresponda ao padrão PRD (ex: `PRD.md`, `prd.md`, `product_requirements.md`, `docs/prd.md`), THE Leitor SHALL armazenar seu conteúdo normalizado no Estado como `prd_content`, aplicando a mesma normalização definida no critério 2.
4. THE Leitor SHALL consolidar o conteúdo de todos os Documentos lidos em `merged_context`, separando cada seção com um cabeçalho contendo o caminho relativo do arquivo de origem como identificador.
5. IF um arquivo listado em `discovered_files` não puder ser lido por erro de permissão, falha de decodificação de caracteres ou tamanho superior ao limite permitido, THEN THE Leitor SHALL registrar o erro no campo `errors` com indicação do arquivo afetado e do motivo da falha, e continuar o processamento com os arquivos restantes.
6. IF `merged_context` estiver vazio após a tentativa de leitura de todos os arquivos, THEN THE Leitor SHALL interromper o fluxo com mensagem `"Não foi possível ler nenhum conteúdo dos documentos encontrados."`.
7. IF um arquivo listado em `discovered_files` não estiver codificado em UTF-8, THEN THE Leitor SHALL tentar decodificá-lo usando Latin-1 como fallback antes de registrar erro de decodificação.

---

### Requirement 5: Análise de Documentação

**User Story:** Como usuário, quero que o agente avalie o conteúdo da documentação encontrada, para que eu obtenha um diagnóstico objetivo da sua qualidade.

#### Acceptance Criteria

1. WHEN `merged_context` estiver disponível no Estado, THE Analisador SHALL avaliar o conteúdo quanto a: clareza (estrutura de seções, uso de linguagem objetiva e presença de exemplos), cobertura de escopo (se abrange propósito, instalação, uso e contribuição), consistência interna (ausência de contradições entre seções) e presença de informações essenciais para onboarding (pré-requisitos, passo a passo de configuração, dependências e instruções de execução).
2. WHEN a avaliação das dimensões estiver concluída, THE Analisador SHALL identificar e listar no mínimo 1 e no máximo 10 pontos fortes presentes na documentação analisada, cada um com uma descrição de até 280 caracteres.
3. WHEN a avaliação das dimensões estiver concluída, THE Analisador SHALL identificar e listar os problemas encontrados, classificando cada item como "observação" (fato verificável sem juízo de ação) ou "recomendação" (sugestão de melhoria acionável), com no mínimo 1 e no máximo 15 itens no total.
4. THE Analisador SHALL produzir uma nota qualitativa em escala inteira de 0 a 10, onde 0-3 indica documentação insuficiente, 4-6 indica documentação parcial com lacunas relevantes, e 7-10 indica documentação adequada, acompanhada de justificativa com no mínimo 2 frases referenciando os achados da análise.
5. THE Analisador SHALL registrar no Estado, no campo `analysis_result`, o resultado estruturado da análise contendo obrigatoriamente os campos: dimensões avaliadas com parecer por dimensão, lista de pontos fortes, lista de problemas classificados, nota com justificativa, e lista de limitações da análise.
6. IF `merged_context` contiver menos de 100 caracteres, THEN THE Analisador SHALL sinalizar no `analysis_result` que a base documental é insuficiente para uma análise completa, registrar uma limitação correspondente, e atribuir nota máxima de 3.
7. IF alguma das quatro dimensões de avaliação não puder ser analisada por ausência de conteúdo correspondente no `merged_context`, THEN THE Analisador SHALL registrar a dimensão como "não avaliável" no `analysis_result` e incluir essa limitação na lista de limitações.

---

### Requirement 6: Geração de Relatório

**User Story:** Como usuário, quero receber um relatório estruturado e legível com o resultado da análise, para que eu entenda claramente o estado da documentação do projeto.

#### Acceptance Criteria

1. WHEN `analysis_result` estiver disponível no Estado, THE Construtor_Relatorio SHALL gerar um Relatório em formato Markdown contendo as seguintes seções na ordem apresentada: Resumo Executivo, Escopo Identificado, Pontos Fortes, Problemas Encontrados, Checklist de Melhorias, Nota Qualitativa e Limitações da Análise, onde cada seção é delimitada por um heading Markdown de nível 2 (`##`).
2. THE Construtor_Relatorio SHALL incluir no Relatório a nota qualitativa como um valor numérico inteiro na escala de 0 a 10, acompanhada de uma justificativa textual com no mínimo 1 frase explicando os fatores que determinaram a nota atribuída.
3. THE Construtor_Relatorio SHALL incluir na seção de Limitações toda informação registrada como limitação durante a análise, incluindo casos de base documental insuficiente.
4. THE Construtor_Relatorio SHALL incluir no Relatório o caminho relativo de cada arquivo analisado para rastreabilidade.
5. THE Construtor_Relatorio SHALL armazenar o Relatório gerado no Estado como `final_report`.
6. THE Construtor_Relatorio SHALL gerar o Relatório de forma que cada seção contenha contexto suficiente para leitura independente, sem exigir acesso aos Documentos originais, incluindo menção explícita ao nome do projeto e ao tipo de documentos analisados.
7. IF `analysis_result` estiver ausente ou incompleto no Estado, THEN THE Construtor_Relatorio SHALL registrar um erro no campo `errors` do Estado e gerar um Relatório parcial contendo apenas as seções Resumo Executivo e Limitações da Análise, indicando quais etapas da análise não foram concluídas.

---

### Requirement 7: Exibição do Resultado

**User Story:** Como usuário, quero visualizar o relatório gerado diretamente na interface, para que eu não precise abrir arquivos externos.

#### Acceptance Criteria

1. WHEN `final_report` estiver disponível no Estado, THE Interface SHALL limpar qualquer conteúdo anterior da área de resultado e renderizar o Relatório em formato Markdown na área de resultado da tela.
2. WHEN o fluxo for interrompido por erro de validação, THE Interface SHALL exibir a `validation_message` correspondente na área de resultado, sem renderizar Relatório.
3. WHEN o fluxo for interrompido por ausência de documentos ou falha de leitura, THE Interface SHALL exibir todas as mensagens registradas em `errors` na área de resultado, cada mensagem em linha separada.
4. WHILE o processamento estiver em execução (desde a submissão até a exibição do resultado ou erro), THE Interface SHALL exibir um indicador de carregamento na área de resultado.
5. IF o processamento não produzir resultado nem erro dentro de 120 segundos, THEN THE Interface SHALL encerrar o indicador de carregamento e exibir mensagem de erro indicando timeout na área de resultado.

---

### Requirement 8: Gerenciamento de Estado

**User Story:** Como desenvolvedor, quero que o Estado seja propagado de forma consistente entre os nós do Grafo, para que cada etapa do fluxo tenha acesso apenas aos dados necessários e corretos.

#### Acceptance Criteria

1. THE Estado SHALL conter os campos: `raw_input` (str), `input_type` (str), `validation_status` (str), `validation_message` (str), `repository_url` (str ou None), `local_files` (list), `discovered_files` (list), `readme_content` (str ou None), `prd_content` (str ou None), `merged_context` (str ou None), `analysis_result` (str ou None), `final_report` (str ou None) e `errors` (list de dicionários contendo pelo menos os campos `node` e `message`), todos inicializados com valores padrão vazios ou None na criação do Estado.
2. WHEN um Nó produzir um resultado, THE Agente SHALL atualizar exclusivamente os campos designados àquele Nó conforme o mapeamento: `receive_input` escreve em `raw_input` e `input_type`; `validate_input` escreve em `validation_status` e `validation_message` e `repository_url` e `local_files`; `discover_docs` escreve em `discovered_files`; `read_docs` escreve em `readme_content` e `prd_content`; `analyze_docs` escreve em `merged_context` e `analysis_result`; `build_report` escreve em `final_report`; qualquer Nó pode adicionar entradas ao campo `errors`.
3. THE Estado SHALL ser tipado com anotações de tipo Python (typing) para todos os seus campos, utilizando TypedDict ou dataclass com todos os campos explicitamente anotados.
4. IF um Nó encontrar um erro que impede a execução dos Nós subsequentes (entrada inválida, falha de leitura de repositório, ou ausência total de documentação descoberta), THEN THE Agente SHALL adicionar um dicionário com os campos `node` (nome do Nó que falhou) e `message` (descrição do erro) ao campo `errors` do Estado e encerrar o fluxo sem executar os Nós seguintes, preservando no Estado todos os campos já preenchidos pelos Nós anteriores.
5. IF o fluxo for encerrado por erro irrecuperável, THEN THE Agente SHALL retornar o Estado parcial contendo os campos preenchidos até o ponto de falha e o campo `errors` populado, sem propagar valores None ou vazios como se fossem resultados válidos para exibição ao usuário.

---

### Requirement 9: Separação de Responsabilidades

**User Story:** Como desenvolvedor, quero que a Interface, o Agente, as Ferramentas e o Estado estejam em módulos separados, para que o projeto seja manutenível e testável.

#### Acceptance Criteria

1. THE Agente SHALL ser implementado nos módulos `app/agent/graph.py`, `app/agent/state.py` e `app/agent/nodes/`, sem declarações de importação (import) oriundas do módulo `app/ui/`.
2. THE Interface SHALL ser implementada exclusivamente no módulo `app/ui/gradio_app.py` e não SHALL conter chamadas diretas a nós do grafo, manipulação do estado do agente, nem regras de validação ou análise de documentação.
3. THE Ferramenta `validate_repository_url` SHALL ser implementada no módulo `app/tools/repo_tools.py`.
4. THE Ferramenta `clone_or_open_repository` SHALL ser implementada no módulo `app/tools/repo_tools.py`.
5. THE Ferramenta `find_documentation_files` SHALL ser implementada no módulo `app/tools/file_tools.py`.
6. THE Ferramenta `read_markdown_file` SHALL ser implementada no módulo `app/tools/file_tools.py`.
7. THE Ferramenta `normalize_document_text` SHALL ser implementada no módulo `app/tools/text_tools.py`.
8. THE Ferramenta `generate_report_markdown` SHALL ser implementada no módulo `app/services/report_service.py`.
9. THE projeto SHALL manter uma direção de dependência unidirecional onde `app/ui/` depende de `app/agent/` e `app/agent/` depende de `app/tools/` e `app/services/`, sem dependências circulares entre esses módulos.
10. WHEN qualquer módulo em `app/agent/`, `app/tools/` ou `app/services/` for importado isoladamente, THE interpretador Python SHALL carregá-lo sem erros de importação e sem exigir que `app/ui/` esteja presente.

---

### Requirement 10: Segurança e Confiabilidade

**User Story:** Como usuário, quero que o sistema opere de forma segura e previsível, para que meus dados e o ambiente de execução não sejam comprometidos.

#### Acceptance Criteria

1. WHEN o usuário submeter uma entrada, THE Agente SHALL validar que a entrada não é vazia, que URLs seguem formato válido de repositório Git e que arquivos enviados possuem extensão `.md`, rejeitando entradas inválidas com mensagem indicando o motivo da rejeição antes de qualquer operação de leitura ou clonagem.
2. IF o processamento de um Repositório ou arquivo produzir uma exceção não tratada, THEN THE Agente SHALL capturar a exceção, registrar a mensagem de erro no campo `errors` do Estado, preservar o Estado acumulado até o ponto de falha sem corrompê-lo e encerrar o fluxo exibindo ao usuário uma mensagem que indique qual etapa falhou e o tipo de erro ocorrido.
3. THE Agente SHALL garantir que credenciais, tokens e variáveis de ambiente cujo nome contenha padrões como `KEY`, `SECRET`, `TOKEN` ou `PASSWORD` não sejam incluídos em logs, no Estado ou no Relatório gerado.
4. WHERE variáveis de ambiente externas forem necessárias, THE Agente SHALL documentar cada variável requerida no arquivo `.env.example` com o nome da variável e uma descrição de uso em comentário.
5. IF uma operação de clonagem de repositório ou leitura de arquivo não for concluída em até 60 segundos, THEN THE Agente SHALL cancelar a operação, registrar timeout no campo `errors` do Estado e encerrar o fluxo com mensagem indicando que o tempo limite foi excedido.
6. IF a clonagem de um repositório falhar ou o fluxo for encerrado por erro, THEN THE Agente SHALL remover o diretório temporário criado para a clonagem antes de finalizar a execução.
