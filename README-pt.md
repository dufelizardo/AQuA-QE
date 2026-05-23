# AQuA-QE System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![AI](https://img.shields.io/badge/AI-Native-purple?style=for-the-badge&logo=openai&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-DDD%20%7C%20Clean%20Architecture-black?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-Pytest-success?style=for-the-badge&logo=pytest)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

![GitHub Repo stars](https://img.shields.io/github/stars/dufelizardo/AQuA-QE?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/dufelizardo/AQuA-QE?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/dufelizardo/AQuA-QE?style=for-the-badge)

## ![visitors](https://visitor-badge.laobi.icu/badge?page_id=dufelizardo/AQuA-QE.visitor-badge)

</div>

**AI-Native Requirements Engineering & Quality Platform**

> Transforma informações não estruturadas em requisitos rastreáveis, validados, testáveis e acessíveis ao longo de todo o SDLC.

---

## O que é o AQuA-QE?

O AQuA-QE é uma plataforma orientada ao ciclo de vida de software que substitui o processo manual de engenharia de requisitos por um pipeline cognitivo assistido por IA. A partir de texto livre — atas de reunião, histórias de usuário, transcrições, documentos — o sistema extrai requisitos estruturados, valida sua qualidade, detecta ambiguidades, gera cenários BDD, verifica conformidade WCAG e mantém rastreabilidade bidirecional completa entre todos os artefatos.

**Capacidades do MVP:**

- Elicitação guiada via interface conversacional
- Extração e classificação de requisitos (RF, RNF, RN, Constraint, Assumption)
- Validação semântica com score de qualidade em 4 dimensões
- Geração automática de cenários BDD com técnicas formais (equivalência, valor limite, tabela de decisão)
- Rastreabilidade bidirecional: requisito ↔ AC ↔ teste ↔ regra de negócio
- Análise de acessibilidade WCAG 2.1/2.2 (A, AA, AAA) com heurísticas Nielsen
- Quality gate consolidado com 7 dimensões e políticas configuráveis
- Memória organizacional com aprendizado incremental de padrões
- Modo mock sem API keys — pipeline completo funciona para desenvolvimento

---

## Início rápido

### Pré-requisitos

- Python 3.11+
- pip ou [Poetry](https://python-poetry.org/)
- Node.js 20+ (apenas para o frontend)

### 1. Clonar e instalar

```bash
git clone https://github.com/sua-org/aqua-qe.git
cd aqua-qe

# Opção A — pip direto
pip install fastapi uvicorn sqlalchemy alembic pydantic httpx python-dotenv

# Opção B — poetry
poetry install
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` e configure ao menos uma das chaves:

```env
ANTHROPIC_API_KEY=sk-ant-...   # Claude (preferido)
OPENAI_API_KEY=sk-proj-...     # OpenAI (fallback automático)
```

> **Sem API keys?** O sistema opera em **modo mock** — respostas JSON fixas são retornadas. O pipeline completo funciona para desenvolvimento e testes.

### 3. Inicializar o banco

```bash
# Cria as 19 tabelas SQLite
python -c "
from persistence.base import build_engine, create_all_tables
create_all_tables(build_engine())
print('Banco inicializado.')
"

# Ou via Alembic (recomendado para produção)
alembic upgrade head
```

### 4. Iniciar a API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Docker

```bash
# Copiar e configurar variáveis
cp .env.example .env
# Editar .env com suas API keys

# Subir API + Frontend
docker compose up -d --build

# Verificar status
docker compose ps
docker compose logs -f api
```

Serviços:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000

---

## Testes

```bash
# Suite completa (60 testes)
ANTHROPIC_API_KEY=mock OPENAI_API_KEY=mock \
python -m pytest tests/ -v

# Por camada
python -m pytest tests/unit/       # invariantes de domínio
python -m pytest tests/integration/ # pipeline de elicitação
python -m pytest tests/api/        # endpoints HTTP

# Com cobertura
python -m pytest tests/ --cov=. --cov-report=term-missing
```

---

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET`  | `/health` | Health check |
| `POST` | `/api/v1/requirements/projects` | Criar projeto |
| `POST` | `/api/v1/requirements/projects/{id}/elicit` | Elicitar requisitos via LLM |
| `PATCH`| `/api/v1/requirements/{id}/refine` | Refinar requisito |
| `POST` | `/api/v1/requirements/{id}/approve` | Aprovar requisito |
| `POST` | `/api/v1/requirements/projects/{id}/approve-all` | Aprovação em lote |
| `GET`  | `/api/v1/requirements/projects/{id}` | Listar requisitos do projeto |

### Exemplo de uso

```bash
# 1. Criar projeto
curl -X POST http://localhost:8000/api/v1/requirements/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Sistema Bancário", "domain": "financeiro"}'

# 2. Elicitar requisitos a partir de texto livre
curl -X POST http://localhost:8000/api/v1/requirements/projects/{project_id}/elicit \
  -H "Content-Type: application/json" \
  -d '{
    "raw_input": "O usuário deve fazer login com CPF e senha. Após 3 tentativas incorretas, a conta deve ser bloqueada por 30 minutos.",
    "language": "pt"
  }'

# 3. Aprovar requisito
curl -X POST http://localhost:8000/api/v1/requirements/{req_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "tech-lead"}'
```

---

## Estrutura do projeto

```
aqua-qe/
├── main.py                    # Entry point FastAPI
├── persistence/base.py        # Engine SQLAlchemy, sessão, Base declarativa
├── shared/
│   ├── event_bus.py           # IEventBus + InProcessEventBus
│   └── wiring.py              # Container de dependências (todos os contextos)
│
├── requirements/              # Contexto upstream — fonte de verdade
│   ├── contracts/             # RequirementSnapshot, IRequirementReader, events
│   ├── domain/                # Entidades, value objects (QualityScore, RequirementVersion)
│   ├── application/           # CreateRequirement, RefineRequirement, ApproveRequirement
│   └── infrastructure/        # Models SQLAlchemy, Repository, Reader, Mappers
│
├── validation/                # Valida semântica + heurísticas
├── testing/                   # Gera BDD com técnicas formais
├── traceability/              # Rastreabilidade bidirecional (BFS)
├── accessibility/             # WCAG 2.1/2.2 + heurísticas Nielsen
├── quality/                   # Quality gate — agrega todos os contextos
├── knowledge/                 # Memória organizacional + ACL
├── ai_gateway/                # Claude + OpenAI + router + fallback + ACL
│
├── api/requirements/          # FastAPI router + Pydantic schemas
├── tests/
│   ├── unit/                  # Domínio puro (sem I/O)
│   ├── integration/           # Pipeline completo
│   └── api/                   # Contratos HTTP
│
├── migrations/                # Alembic env.py + versions/
├── Dockerfile.api
├── Dockerfile.frontend
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## Comandos make

```bash
make dev          # Inicia API com reload
make test         # Suite completa
make test-unit    # Apenas unitários
make test-int     # Apenas integração
make test-api     # Apenas API HTTP
make lint         # Ruff check
make db-upgrade   # Aplica migrations
make db-migrate MSG="desc"  # Gera nova migration
make db-reset     # Reseta banco (dev)
make docker       # Sobe via docker compose
make docker-down  # Para containers
make docker-logs  # Acompanha logs
make clean        # Remove cache
```

---

## Configuração avançada

### Variáveis de ambiente completas

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `ANTHROPIC_API_KEY` | — | Chave Claude (preferido para extração/validação/geração) |
| `OPENAI_API_KEY` | — | Chave OpenAI (fallback automático + scoring) |
| `DATABASE_URL` | `sqlite:///./aqua_qe.db` | URL do banco (SQLite no MVP) |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CORS_ORIGINS` | `*` | Origens permitidas para o frontend |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL da API acessível pelo browser |
| `ENV` | `production` | Ambiente (`development`, `production`) |

### Roteamento LLM

O AI Gateway roteia automaticamente por tipo de operação:

| Operação | Provider padrão | Fallback |
|----------|----------------|---------|
| Extração de requisitos | Claude | OpenAI |
| Validação semântica | Claude | OpenAI |
| Geração de testes BDD | Claude | OpenAI |
| Scoring de qualidade | OpenAI | Claude |
| Análise WCAG | Claude | OpenAI |

Se nenhum provider estiver disponível, o sistema retorna respostas mock estruturadas.

### Migração para PostgreSQL (Fase 2+)

```env
DATABASE_URL=postgresql+psycopg2://aquaqe:senha@localhost:5432/aquaqe
```

Nenhuma mudança de código necessária — a camada de persistência é abstraída via repositórios.

---

## Contribuindo

### Adicionando um novo bounded context

1. Criar estrutura `novo_contexto/{contracts.py, domain/, application/, infrastructure/}`
2. Implementar `contracts.py` com DTOs, interface de serviço e eventos de domínio
3. Criar model SQLAlchemy com prefixo de tabela (`nvc_`)
4. Registrar model em `persistence/base.py` → `create_all_tables()`
5. Registrar model em `migrations/env.py`
6. Gerar migration: `make db-migrate MSG="add_novo_contexto"`
7. Registrar handlers em `shared/wiring.py`
8. Adicionar testes em `tests/unit/` e `tests/integration/`

### Princípios de arquitetura

- **Sem imports cruzados de domínio**: contextos se comunicam apenas via contratos (`contracts.py`), eventos de domínio ou interfaces
- **ACL obrigatória** para `knowledge/` e `ai_gateway/` — nunca chamados diretamente
- **Repositório é a única classe** com acesso ao banco em cada contexto
- **Entidades de domínio são POPO** (Plain Old Python Objects) — sem imports de SQLAlchemy
- **Handlers são funções**, não classes — retornados por factories que capturam dependências via closure

---

## Licença

MIT — consulte `LICENSE` para detalhes.
