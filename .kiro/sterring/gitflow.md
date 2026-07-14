# GitFlow Steering

## Objetivo
Garantir consistência no fluxo de versionamento do projeto utilizando a estratégia GitFlow.

---

## Estrutura de Branches

### Main
- Contém apenas código estável e pronto para produção
- Cada merge deve representar uma release

### Develop
- Branch principal de desenvolvimento
- Integra features antes de promoção para produção

### Feature
Padrão:

feature/nome-da-feature

Exemplos:
- feature/login-social
- feature/dashboard-financeiro

Regras:
- Criar sempre a partir de `develop`
- Merge de volta para `develop`

---

### Release
Padrão:

release/x.y.z

Exemplo:
release/1.4.0

Regras:
- Criada a partir de `develop`
- Apenas ajustes finais
- Merge em `main` e `develop`

---

### Hotfix
Padrão:

hotfix/descricao

Exemplo:
hotfix/correcao-token-expirado

Regras:
- Criada a partir de `main`
- Merge em `main` e `develop`

---

### Bugfix (em desenvolvimento)
Padrão:

feature/fix-descricao

Exemplo:
- feature/fix-calculo-indice
- feature/fix-validacao-lead

Regras:
- Criar sempre a partir de `develop`
- Merge de volta para `develop`
- Não criar branches `bugfix/` separadas na v1

> ℹ️ Correções de bugs em desenvolvimento seguem o mesmo fluxo de feature branches.
> Apenas bugs em produção utilizam `hotfix/`.

---

## Convenção de Commits

Utilizar Conventional Commits.

Formato:

tipo(escopo): descrição

Exemplos:
- feat(auth): adiciona login com Google
- fix(api): corrige timeout na autenticação
- refactor(ui): simplifica componente de botão
- docs(readme): atualiza instruções

Tipos permitidos:
- feat
- fix
- refactor
- docs
- test
- chore
- perf

---

## Pull Requests

Todo PR deve conter:

1. Objetivo da alteração
2. Branch de origem e destino
3. Checklist:
   - Testado localmente
   - Testes automatizados passando (domínio e serviços)
   - Sem conflitos
   - Segue padrão de commits

---

## Regras para IA / Automação

Ao sugerir branches:
- Sempre respeitar nomenclatura GitFlow

Ao gerar commits:
- Utilizar Conventional Commits

Ao sugerir merges:
- Nunca sugerir merge direto em `main`, exceto release/hotfix

Ao corrigir bugs:
- Se produção → hotfix
- Se desenvolvimento → fix dentro de feature branch