# Product Requirements Document (PRD)
## Feedloop — Totem Edition

---

## 1. Visão do Produto

### 1.1 Definição do Produto
O **Feedloop — Totem Edition** é um aplicativo Flutter standalone projetado para totens interativos em eventos corporativos. O sistema permite coleta de feedback anônimo de participantes com geração automática de insights via IA local, operando completamente offline.

### 1.2 Problema Resolvido
Em grandes eventos corporativos (SeniorTec, Universo TOTVS, Senior Experience, CONARH), gestores de produto não possuem um canal eficiente para capturar demandas, expectativas e percepções de clientes, vendedores e usuários em tempo real. O feedback se perde em conversas informais ou pesquisas enviadas por e-mail dias depois, resultando em perda de oportunidades valiosas.

### 1.3 Objetivos do Produto
- **Captura em tempo real**: Coletar feedback durante o evento quando a experiência está fresca na mente dos participantes
- **Anonimato garantido**: Permitir feedback honesto sem identificação pessoal
- **Insights automáticos**: Gerar análises acionáveis via IA local sem dependência de conectividade
- **Operação autônoma**: Funcionar completamente offline em modo kiosk seguro
- **Conformidade LGPD**: Garantir proteção de dados através de anonimato total

---

## 2. Funcionalidades

### 2.1 Funcionalidades Principais

#### F-001: Modo Kiosk Seguro
- Interface travada durante o evento impedindo acesso ao sistema operacional
- Desbloqueio via gesto oculto (5 toques no logo) + senha SHA-256
- Retorno automático ao modo kiosk após timeout de inatividade

#### F-002: Coleta de Feedback Anônimo
- Seleção de origem: Cliente, Vendedor, Serviço (sem identificação pessoal)
- Suporte a múltiplos tipos de pergunta: abertas, múltipla escolha, avaliação
- Validação de completude antes do envio
- Confirmação visual com retorno automático à tela inicial

#### F-003: Configuração de Eventos
- Criação de eventos com nome, data e senha master
- Configuração de perguntas personalizadas com reordenação
- Ativação/desativação de eventos (apenas um ativo por vez)
- Validação de integridade dos dados de configuração

#### F-004: Análise e Insights de IA
- Processamento local de feedbacks sem APIs externas
- Análise por origem das demandas (cliente/vendedor/serviço)
- Extração de palavras-chave excluindo stop words em português
- Geração de sugestões acionáveis baseadas em padrões identificados

#### F-005: Visualização de Resultados
- Painel com panorama numérico (total, abertas, concluídas)
- Lista de feedbacks com filtros por origem e status
- Detalhamento completo de cada feedback com respostas associadas
- Interface de insights com sugestões categorizadas

#### F-006: Exportação de Dados
- Geração de arquivos CSV com metadados do evento
- Exportação JSON estruturada incluindo respostas detalhadas
- Compartilhamento via e-mail ou drive através do sistema operacional
- Controle de acesso restrito ao usuário master autenticado

### 2.2 Funcionalidades Secundárias

#### F-007: Gestão de Estado
- Persistência local via SQLite com transações ACID
- Sincronização de estado entre providers (Event, Feedback, Insights, Kiosk)
- Recuperação automática de falhas de banco de dados
- Backup local automático dos dados críticos

#### F-008: Interface Adaptativa
- Design responsivo para tablets 10"+ em orientação landscape
- Tema Material Design 3 com cores corporativas
- Componentes reutilizáveis (DemandCard, InsightCard, Badges)
- Acessibilidade com áreas tocáveis mínimas de 48dp

---

## 3. Regras de Negócio

### 3.1 Gestão de Eventos
- **RN-001**: Apenas um evento pode estar ativo simultaneamente no sistema
- **RN-002**: Criação de novo evento desativa automaticamente o anterior
- **RN-003**: Eventos não podem ser excluídos, apenas desativados para auditoria
- **RN-004**: Evento ativo automaticamente ativa modo kiosk na inicialização

### 3.2 Coleta de Feedback
- **RN-005**: Todo feedback deve ser completamente anônimo (sem dados pessoais)
- **RN-006**: Origem é obrigatória mas não identifica indivíduo específico
- **RN-007**: Todas as perguntas configuradas devem ser respondidas
- **RN-008**: Status inicial de todo feedback é "aberta"
- **RN-009**: Apenas usuário master pode alterar status para "concluída"

### 3.3 Segurança e Privacidade
- **RN-010**: Nenhum dado pessoal (nome, e-mail, CPF, telefone) pode ser coletado
- **RN-011**: Senhas master devem ter mínimo 4 caracteres e são hasheadas SHA-256
- **RN-012**: Modo kiosk deve bloquear acesso a outras aplicações
- **RN-013**: Timeout automático retorna ao modo kiosk após 30 segundos de inatividade
- **RN-014**: Dados permanecem exclusivamente no dispositivo local

### 3.4 Processamento de IA
- **RN-015**: Insights são gerados apenas com dados do evento ativo
- **RN-016**: Mínimo de 3 feedbacks necessário para insights significativos
- **RN-017**: Processamento deve ser 100% local sem dependências externas
- **RN-018**: Insights são recalculados automaticamente a cada novo feedback

### 3.5 Exportação e Auditoria
- **RN-019**: Exportação disponível apenas para usuário master autenticado
- **RN-020**: Dados exportados devem incluir metadados completos do evento
- **RN-021**: Formatos suportados limitados a CSV e JSON
- **RN-022**: Exportação desabilitada quando não há feedbacks no evento

---

## 4. Fluxos Funcionais

### 4.1 Fluxo do Participante (Modo Kiosk)
```
Início → Tela Boas-vindas → Seleção Origem → Pesquisa → Confirmação → Agradecimento → Retorno Início
```

### 4.2 Fluxo do Master (Modo Administrativo)
```
Desbloqueio → Painel Principal → [Configuração|Visualização|Insights|Exportação] → Retorno Kiosk
```

### 4.3 Fluxo de Processamento de IA
```
Novo Feedback → Análise Origem → Extração Keywords → Geração Insights → Atualização Interface
```

---

## 5. Requisitos Funcionais

- **RF-001**: Sistema deve operar em modo kiosk bloqueando acesso ao SO
- **RF-002**: Interface deve ser otimizada para tablets 10"+ em landscape
- **RF-003**: Áreas tocáveis devem ter mínimo 48dp conforme Material Design
- **RF-006**: Sistema deve suportar perguntas abertas, múltipla escolha e avaliação
- **RF-011**: IA local deve processar feedbacks em tempo < 5 segundos
- **RF-016**: Desbloqueio deve exigir gesto oculto + senha SHA-256
- **RF-021**: Sistema deve exportar dados em formatos CSV e JSON
- **RF-024**: Persistência deve usar SQLite com transações ACID

---

## 6. Requisitos Não Funcionais

- **RNF-001**: Tempo de resposta da interface < 200ms
- **RNF-002**: Inicialização do aplicativo < 3 segundos
- **RNF-006**: Disponibilidade 99.9% durante eventos (8 horas)
- **RNF-009**: Operação completamente offline
- **RNF-016**: Anonimato 100% garantido
- **RNF-021**: Suporte Android 7.0+ (API level 24+)
- **RNF-022**: Compatibilidade com tablets 10"+

---

## 7. Restrições

- Plataforma limitada ao Android 7.0+
- Hardware: tablets com mínimo 10" e 2GB RAM
- Operação completamente offline
- Apenas um evento ativo por dispositivo
- Máximo 1000 feedbacks por evento
- Suporte inicial apenas para português brasileiro
