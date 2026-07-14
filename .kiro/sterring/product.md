# Product Steering — Document Analysis Agent

## Nome do produto
Agente de Análise de Documentação de Software

## Visão do produto
Um agente que avalia documentação técnica de software a partir de um repositório Git ou arquivos locais, identificando qualidade, lacunas e melhorias prioritárias em README e PRD.

## Problema
Projetos de software frequentemente possuem documentação incompleta, inconsistente ou pouco útil para onboarding, manutenção e alinhamento entre produto e desenvolvimento. Essa análise costuma ser manual, subjetiva e demorada.

## Solução
Oferecer um agente que automatiza a leitura e análise da documentação, gerando um relatório final estruturado com:
- resumo executivo
- pontos fortes
- problemas encontrados
- checklist de melhorias

## Público-alvo
- Desenvolvedores
- Tech leads
- Product managers
- Estudantes e equipes acadêmicas
- Pessoas avaliando qualidade documental de projetos

## Entradas aceitas
- URL de repositório Git
- Arquivos README.md
- Arquivos PRD.md
- Arquivos equivalentes de documentação em Markdown

## Saída do produto
Relatório estruturado exibido na interface contendo:
- resumo da documentação
- escopo identificado
- pontos fortes
- problemas encontrados
- checklist de melhorias
- nota qualitativa
- limitações da análise

## Fluxo do usuário
1. Usuário informa uma URL de repositório ou envia arquivos.
2. Sistema valida a entrada.
3. Sistema busca e localiza os documentos relevantes.
4. Agente lê README e/ou PRD.
5. Agente analisa conteúdo, clareza, cobertura e consistência.
6. Sistema gera o relatório final.
7. Usuário visualiza o resultado no Gradio.

## Proposta de valor
- Reduz tempo de revisão documental.
- Aumenta consistência da avaliação.
- Facilita onboarding técnico.
- Apoia melhoria contínua de README e PRD.
- Gera evidência clara para apresentação e demonstração do projeto.

## Critérios de qualidade do produto
O produto deve:
- aceitar entradas reais
- validar antes de processar
- usar pelo menos uma ferramenta integrada
- manter contexto no estado
- gerar saída estruturada e útil
- deixar limitações explícitas
- funcionar de forma demonstrável em apresentação

## Regras de produto
- O agente não substitui revisão humana final.
- O agente não deve inventar requisitos ausentes.
- O agente deve sinalizar quando a base documental for insuficiente.
- O agente deve diferenciar observação de recomendação.
- O relatório deve ser compreensível por alguém que não leu os arquivos originais.

## Critérios de sucesso
- O usuário entende rapidamente o estado da documentação analisada.
- O relatório identifica falhas reais e ações concretas.
- A demo mostra fluxo completo de ponta a ponta.
- O projeto atende os critérios acadêmicos de LangGraph, ferramenta, validação, contexto e documentação.

## Possíveis evoluções
- Score por categoria
- comparação entre múltiplos repositórios
- exportação do relatório em `.md` ou `.pdf`
- análise de documentação além de README/PRD
- sugestão automática de trechos reescritos