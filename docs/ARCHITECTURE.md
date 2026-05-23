# AQuA-QE — Documentação Arquitetural

**Versão:** 0.1.0-mvp  
**Arquitetura:** Modular Monolith (com path de evolução para microsserviços)

---

## 1. Visão estratégica

O AQuA-QE é uma plataforma AI-native orientada ao SDLC capaz de transformar informações não estruturadas em ativos inteligentes, rastreáveis, acessíveis, validados e testáveis.

A arquitetura foi projetada com dois objetivos simultâneos: **velocidade de iteração no MVP** (monolito modular com SQLite) e **evolução incremental sem reescrita** (bounded contexts com contratos explícitos, prontos para extração como serviços independentes).

---

## 2. Decisão arquitetural: Modular Monolith

### Justificativa

A escolha do **Modular Monolith** como arquitetura inicial é deliberada e justificada por:

| Fator | Decisão |
|-------|---------|
| Domínio em evolução | Bounded contexts ainda estabilizando — extração prematura gera retrabalho |
| Complexidade operacional | Zero overhead de rede, service discovery, distributed tracing no MVP |
| Integração entre engines cognitivas | Chamadas síncronas in-process — latência imperceptível |
| Iteração rápida | Deploy único, depuração simples, sem contratos de API versionados ainda |

### Path de evolução

A arquitetura permite evolução **sem reescrita do domínio principal**:

```
Fase 0: MVP Monolito (SQLite, in-process event bus)
   ↓
Fase 1: Extração prioritária (Accessibility + Validation → serviços independentes)
   ↓
Fase 2: Extração intermediária (Testing + Traceability → PostgreSQL + Neo4j)
   ↓
Fase 3: Orquestração distribuída (Quality + Knowledge → pgvector, Temporal)
   ↓
Fase 4 (opcional): Plataforma federada (multi-tenant, Knowledge federado)
```

O gatilho para cada fase **não é o tempo** — são critérios objetivos: volume de chamadas justificando deploy isolado, necessidade de tecnologia de persistência específica (Neo4j, pgvector), ou times independentes trabalhando no mesmo contexto.

---

## 3. Visão estrutural

```
Frontend (React / Next.js)
         ↓
API Gateway (FastAPI)
         ↓
Core Application
├── requirements/       ← Upstream central
├── validation/
├── testing/
├── traceability/
├── accessibility/
├── quality/            ← Agregador final
├── knowledge/          ← Transversal (ACL)
├── ai_gateway/         ← Infraestrutura (ACL)
├── persistence/
└── shared/             ← Event bus, wiring, contratos comuns
```

---

## 4. Bounded contexts

### 4.1 Mapa de contextos

```
Requirement Engineering  ──(U→D)──►  Validation
         │               ──(U→D)──►  Traceability
         │               ──(U→D)──►  Test Intelligence
         │
         ▼
   Quality Engineering  ◄── ValidationCompleted
         │              ◄── TestSuiteGenerated
         │              ◄── AccessibilityReportGenerated
         │
   Accessibility ────────────────►  Quality Engineering

   Knowledge (ACL) ◄── todos os contextos via KnowledgeACL
   AI Infrastructure (ACL) ◄── todos os contextos via AIGatewayACL
```

**Padrões de integração utilizados:**

| Padrão | Uso |
|--------|-----|
| Published Language | `RequirementSnapshot` — contrato imutável publicado pelo RE |
| Open Host Service | `IRequirementReader` — interface estável para leitura síncrona |
| Domain Events | `RequirementCreated`, `ValidationCompleted`, `TestSuiteGenerated`... |
| Anti-Corruption Layer | `KnowledgeACL`, `AIGatewayACL` — tradução na borda |

### 4.2 Detalhamento por contexto

#### Requirement Engineering
- **Papel:** Upstream central. Fonte de verdade de todos os outros contextos.
- **Agregado raiz:** `Project`
- **Entidades:** `Requirement`, `AcceptanceCriteria`, `BusinessRule`, `ElicitationSession`
- **Value objects:** `RequirementType`, `Priority`, `QualityScore`, `RequirementVersion`
- **Invariantes principais:**
  - `QualityScore` — todos os scores entre 0 e 100
  - `Requirement.approve()` — bloqueia se `clarity < 60`
  - Refinamento apenas em status `DRAFT` ou `REVIEW`
- **Eventos publicados:** `RequirementCreated`, `RequirementRefined`, `RequirementApproved`, `GapDetected`, `ErsGenerated`
- **Candidato à extração:** Nunca isolado primeiro — é a fonte de verdade de tudo

#### Validation
- **Papel:** Análise de qualidade semântica dos requisitos
- **Duas camadas:** Heurísticas síncronas (sem LLM) + análise LLM
- **Heurísticas:** Termos vagos, campos vazios, RF sem critérios de aceite
- **Invariante:** Issues `CRITICAL` bloqueiam aprovação do requisito
- **Eventos publicados:** `ValidationCompleted`, `CriticalIssueDetected`, `RequirementBlockedByValidation`
- **Candidato à extração:** Fase 1 (regras crescem independentemente)

#### Test Intelligence
- **Papel:** Geração automática de cenários BDD com técnicas formais
- **Técnicas implementadas:** Equivalência, Valor Limite, Tabela de Decisão
- **Pipeline:** Técnicas formais geram `ScenarioBlueprint` → LLM preenche GWT
- **Invariante:** RF MUST requer ao menos um cenário negativo
- **Eventos publicados:** `TestSuiteGenerated`, `CoverageGapDetected`, `AutomationCandidateIdentified`
- **Candidato à extração:** Fase 2 (modelos especializados, múltiplos frameworks)

#### Traceability
- **Papel:** Rastreabilidade bidirecional entre todos os artefatos
- **Modelo:** Tabela polimórfica `trc_links` — sem FK cruzadas para outros contextos
- **Algoritmo:** BFS para análise de impacto
- **Invariante:** Links são imutáveis após criação — invalidação cria novo link com `SUPERSEDES`
- **Evolução:** Neo4j dedicado na Fase 2 — populado por replay de eventos (não por migração direta)
- **Candidato à extração:** Fase 2 (grafo Neo4j quando volume justificar)

#### Accessibility
- **Papel:** Validação WCAG 2.1/2.2 e heurísticas Nielsen
- **Catálogo:** 14 critérios WCAG mapeados + 10 heurísticas de Nielsen
- **Estratégia:** Heurísticas síncronas por palavras-chave → LLM apenas para requisitos com componente UI
- **Conformance:** A → AA (AA é o alvo padrão do MVP)
- **Candidato à extração:** Fase 1 (axe-core, Pa11y exigem processo dedicado)

#### Quality Engineering
- **Papel:** Agregador final — consolida sinais de todos os contextos
- **7 dimensões:** clareza, completude, consistência, rastreabilidade, cobertura, testabilidade, acessibilidade
- **Cross-context queries:** O repositório faz queries SQL em tabelas de outros contextos (legítimo no monolito)
- **Invariante:** `QualityReport` é imutável após emissão — revisões criam nova instância com `previous_report_id`
- **Hash de integridade:** SHA-256 do conteúdo para auditoria
- **Candidato à extração:** Fase 3 (depois que todos os upstream estiverem estáveis)

#### Knowledge
- **Papel:** Memória organizacional transversal
- **Aprendizado:** Padrões promovidos após `usage_count >= 3` em projetos distintos
- **Similaridade no MVP:** Jaccard sobre tokens (sem LLM, sem vetor)
- **Evolução:** pgvector na Fase 3 → `embedding` é `nullable` até lá
- **ACL obrigatória:** Nenhum contexto instancia `KnowledgeContribution` diretamente

#### AI Infrastructure
- **Papel:** Abstração de provedores LLM
- **Providers:** Claude (preferido), OpenAI (fallback automático), mock (sem API keys)
- **Roteamento:** Por `PromptPurpose` → provider preferido definido em `_ROUTING`
- **Cache:** In-process com TTL por propósito (300s a 1800s)
- **Auditoria:** Log estruturado JSON de toda chamada (context_id, tokens, latência, custo)
- **ACL obrigatória:** `AIGatewayACL` é a única porta de entrada para todos os contextos

---

## 5. Fluxo cognitivo

O pipeline transforma entrada bruta em artefatos em 16 etapas agrupadas em 5 fases:

```
Entrada bruta (texto, docs, atas, histórias)
        ↓
[INGESTÃO]
1. Normalização (encoding, idioma, tipo)
2. Persistência da sessão de elicitação

[PROCESSAMENTO SEMÂNTICO]
3. Análise semântica via LLM (intenção, domínio)
4. Extração de entidades (atores, ações, objetos, regras)
5. Classificação de requisitos (RF/RNF/RN/Constraint/Assumption)
6. Detecção de gaps (completude, padrões organizacionais)
7. Perguntas complementares → loop de elicitação

[VALIDAÇÃO E QUALIDADE]
8. Validação heurística (termos vagos, campos vazios, AC ausentes)
9. Análise semântica LLM (ambiguidades, inconsistências)
10. Análise de acessibilidade (WCAG heurístico + LLM para UI)

[GERAÇÃO DE ARTEFATOS]
11. Rastreabilidade (links requisito ↔ AC ↔ RN)
12. Geração de cenários BDD (blueprints de técnicas + LLM)
13. Validação de cobertura (MUST sem negativo = gap)
14. Quality gate (7 dimensões, policies, hash de integridade)

[PERSISTÊNCIA E MEMÓRIA]
15. Persistência semântica (19 tabelas SQLite)
16. Memória organizacional (padrões aprendidos, promoção por uso)
```

A etapa 7 cria um **loop intencional** — o pipeline não é linear quando há gaps, itera até a completude ser atingida.

---

## 6. Modelo de dados

### Prefixos de tabela por contexto

| Contexto | Prefixo | Tabelas principais |
|----------|---------|-------------------|
| Requirement Engineering | `req_` | `req_projects`, `req_requirements`, `req_acceptance_criteria`, `req_business_rules`, `req_sessions` |
| Validation | `val_` | `val_reports`, `val_issues` |
| Test Intelligence | `tst_` | `tst_suites`, `tst_scenarios` |
| Traceability | `trc_` | `trc_links` |
| Accessibility | `acc_` | `acc_reports`, `acc_wcag_issues`, `acc_heuristic_issues` |
| Quality | `qlt_` | `qlt_reports`, `qlt_dimension_scores`, `qlt_policies` |
| Knowledge | `knw_` | `knw_patterns`, `knw_ontologies` |
| AI Infrastructure | `aig_` | `aig_prompt_logs` |

O prefixo de tabela é a **fronteira de migração**: quando um contexto migra para banco dedicado, as tabelas com seu prefixo são as únicas que precisam de plano de migração.

### Decisões de design do modelo

**`trc_links` é polimórfica por design.** `source_type` e `target_type` aceitam qualquer `ArtifactType` sem FK cruzadas. Integridade referencial cruzada é responsabilidade do domínio, não do banco. Isso permite a extração do Traceability para Neo4j sem migração de dados — apenas replay de eventos.

**`QualityReport` é imutável após emissão.** `integrity_hash` (SHA-256) garante auditoria. Revisões criam nova linha com `previous_report_id` apontando para o anterior.

**`knw_patterns.embedding` é nullable.** No MVP, busca por similaridade usa Jaccard sobre tokens. Na Fase 3, quando pgvector estiver disponível, o campo é populado e a busca migra para cosine similarity sem mudança de schema.

### Path de evolução da persistência

```
Fase 0: SQLite único (todos os contextos no mesmo banco)
   ↓
Fase 1: SQLite separado por contexto extraído (database-per-service preparado)
   ↓
Fase 2: PostgreSQL (relacional) + Neo4j (Traceability)
   ↓
Fase 3: PostgreSQL + pgvector (Knowledge) + Weaviate opcional (cross-tenant)
```

**Princípio de migração:** Schema compartilhado → schemas separados no mesmo banco → bancos próprios após extração. SQLite → PostgreSQL via dump + restore com validação de integridade referencial antes do cutover.

---

## 7. Event Bus e comunicação entre contextos

### No MVP: InProcessEventBus

```python
bus = InProcessEventBus()
bus.subscribe(RequirementCreated, validation_handler)
bus.subscribe(RequirementCreated, traceability_handler)
bus.subscribe(RequirementApproved, testing_handler)
# ...
bus.publish(RequirementCreated(snapshot=snapshot, session_id=session_id))
```

- Handlers executam na mesma thread do publisher (síncrono)
- Falha em um handler **não impede** os demais (isolamento por `try/except`)
- `shared/wiring.py` é o mapa completo de quem assina o quê

### Na Fase 2: broker externo

A interface `IEventBus` é idêntica para `InProcessEventBus` e qualquer broker externo. Trocar Redis Streams por RabbitMQ não exige mudança nos publishers ou handlers — apenas na implementação injetada em `wiring.py`.

### Subscrições registradas

| Evento | Subscribers |
|--------|------------|
| `RequirementCreated` | Validation, Traceability |
| `RequirementRefined` | Validation, Traceability |
| `RequirementApproved` | Testing, Accessibility, Knowledge |
| `TestSuiteGenerated` | Traceability, Quality, Knowledge |
| `ValidationCompleted` | Quality |
| `AccessibilityReportGenerated` | Quality |
| `CoverageGapDetected` | Quality |

---

## 8. AI Gateway

### Roteamento por propósito

```
PromptPurpose.EXTRACTION    → Claude  (fallback: OpenAI)
PromptPurpose.VALIDATION    → Claude  (fallback: OpenAI)
PromptPurpose.GENERATION    → Claude  (fallback: OpenAI)
PromptPurpose.SCORING       → OpenAI  (fallback: Claude)
PromptPurpose.ACCESSIBILITY → Claude  (fallback: OpenAI)
```

### Cache semântico

| Propósito | TTL |
|-----------|-----|
| `extraction` | 5 min |
| `validation` | 10 min |
| `generation` | 15 min |
| `scoring` | 30 min |
| `accessibility` | 15 min |

Chave de cache: SHA-256 de `(purpose + system + user[:200])`.

### ACL — por que é obrigatória

Sem a `AIGatewayACL`, cada contexto construiria seus próprios `PromptRequest` com system prompts potencialmente divergentes. A ACL centraliza:
- System prompts por propósito (versionados implicitamente)
- Parâmetros de temperatura e max_tokens por operação
- Estratégia de custo (`cost_budget`)
- A decisão de qual provider usar

---

## 9. Estrutura de dependências e regras de arquitetura

### Hierarquia de imports permitidos

```
api/          → pode importar: application/, contracts/, shared/
application/  → pode importar: domain/, contracts/, shared/
domain/       → NÃO importa: infrastructure/, application/, api/
infrastructure/ → pode importar: domain/, contracts/, persistence/
contracts/    → pode importar: value_objects de outros contratos, events base
shared/       → pode importar: apenas contratos (sem lógica de domínio)
```

### Regras absolutas

1. **Nenhum contexto lê o banco de outro** — apenas via interface ou evento, desde o dia zero
2. **Entidades de domínio são POPO** — sem imports de SQLAlchemy, FastAPI ou httpx
3. **ACL é a única porta** para `knowledge/` e `ai_gateway/`
4. **Handlers são funções puras** retornadas por factories com dependências capturadas via closure
5. **`shared/` não contém lógica de negócio** — apenas DTOs, eventos, interfaces, event bus e wiring

### Por que a regra 1 é a mais importante

Quem viola "nenhum contexto lê o banco de outro" no monolito paga com semanas de refatoração antes de qualquer extração de serviço. O `QualityRepository` é a **única exceção controlada** — ele faz queries cross-context porque Quality é o agregador final e essa é sua função, explicitamente documentada no código como "legítimo no monolito, vira chamada HTTP na Fase 3".

---

## 10. Critérios de extração por contexto

| Contexto | Fase | Sinal principal | Risco de extração |
|----------|------|----------------|-------------------|
| Accessibility | 1 | axe-core/Pa11y exigem processo dedicado | Baixo — fronteiras limpas |
| Validation | 1 | Regras crescem independentemente do domínio | Médio — divergência semântica |
| Test Intelligence | 2 | Modelos especializados, múltiplos frameworks | Alto — consistência de leitura |
| Traceability | 2 | Grafo Neo4j, consultas dominam carga | Alto — eventual consistency insuficiente |
| Quality | 3 | Todos os upstream estáveis primeiro | Muito alto — agrega tudo |
| Knowledge | 3 | pgvector necessário para escala | Muito alto — latência de leitura síncrona |
| Requirement Engineering | Nunca primeiro | Fonte de verdade de tudo | Só após todos os outros |

**Pré-requisito universal antes de qualquer extração:** contract tests cobrindo todos os eventos que o contexto publica ou consome, com suite rodando em CI.

---

## 11. Decisões de design registradas

### ADR-001: Modular Monolith como arquitetura inicial
- **Decisão:** Começar com monolito modular, não microsserviços
- **Contexto:** Domínio em evolução, time pequeno, pressão por velocidade de validação
- **Consequências:** Iteração rápida agora; extração cirúrgica no futuro por contexto, não por reescrita

### ADR-002: Event bus in-process com interface agnóstica de broker
- **Decisão:** `InProcessEventBus` implementa `IEventBus` — mesma interface do broker externo
- **Contexto:** Desacoplamento temporal necessário, overhead de broker desnecessário no MVP
- **Consequências:** Migração para Redis Streams/RabbitMQ não exige mudança nos publishers ou handlers

### ADR-003: Tabela de rastreabilidade polimórfica sem FK cruzadas
- **Decisão:** `trc_links` referencia artefatos por `(type, id, version)` sem FK para outras tabelas
- **Contexto:** Links existem entre artefatos de contextos diferentes — FK cruzadas acoplariam schemas
- **Consequências:** Integridade referencial é responsabilidade do domínio; extração para Neo4j via replay de eventos (não migração direta)

### ADR-004: QualityRepository com cross-context queries
- **Decisão:** `QualityRepository` faz queries SQL em tabelas de outros contextos diretamente
- **Contexto:** Quality é o agregador final — precisa de dados de Validation, Testing, Traceability, Accessibility
- **Consequências:** Acoplamento controlado e documentado; na Fase 3, cada query vira chamada HTTP para a API do contexto correspondente

### ADR-005: `embedding` nullable no Knowledge
- **Decisão:** Campo `embedding` é `Optional[List[float]]` e `nullable` no banco
- **Contexto:** pgvector não disponível no MVP; busca Jaccard é suficiente para volume inicial
- **Consequências:** Migração para busca vetorial não exige mudança de schema — apenas popular o campo e trocar a implementação de `find_similar`

### ADR-006: ACL obrigatória para Knowledge e AI Infrastructure
- **Decisão:** Nenhum contexto instancia `KnowledgeContribution` ou `PromptRequest` diretamente
- **Contexto:** Esses dois contextos têm vocabulário próprio que não deve vazar para o domínio de negócio
- **Consequências:** Mudanças no AI Gateway (novo provider, novo formato de prompt) não impactam nenhum contexto de negócio; mudanças no schema de conhecimento ficam isoladas na ACL
