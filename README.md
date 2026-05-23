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

---

**AI-Native Requirements Engineering & Quality Platform**

> Transforms unstructured information into traceable, validated, testable, and accessible requirements throughout the entire SDLC.

---

## What is AQuA-QE?

AQuA-QE is a software lifecycle-oriented platform that replaces the manual requirements engineering process with an AI-assisted cognitive pipeline. From free-form text — meeting notes, user stories, transcripts, and documents — the system extracts structured requirements, validates their quality, detects ambiguities, generates BDD scenarios, verifies WCAG compliance, and maintains complete bidirectional traceability across all artifacts.

**MVP Capabilities:**

* Guided elicitation through a conversational interface
* Requirement extraction and classification (FR, NFR, BR, Constraint, Assumption)
* Semantic validation with a 4-dimensional quality score
* Automatic BDD scenario generation using formal techniques (equivalence partitioning, boundary value analysis, decision tables)
* Bidirectional traceability: requirement ↔ AC ↔ test ↔ business rule
* WCAG 2.1/2.2 accessibility analysis (A, AA, AAA) with Nielsen heuristics
* Consolidated quality gate with 7 dimensions and configurable policies
* Organizational memory with incremental pattern learning
* Mock mode without API keys — full pipeline works for development

---

## Quick Start

### Prerequisites

* Python 3.11+
* pip or [Poetry](https://python-poetry.org/?utm_source=chatgpt.com)
* Node.js 20+ (frontend only)

### 1. Clone and install

```bash
git clone https://github.com/your-org/aqua-qe.git
cd aqua-qe

# Option A — direct pip
pip install fastapi uvicorn sqlalchemy alembic pydantic httpx python-dotenv

# Option B — poetry
poetry install
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and configure at least one key:

```env
ANTHROPIC_API_KEY=sk-ant-...   # Claude (preferred)
OPENAI_API_KEY=sk-proj-...     # OpenAI (automatic fallback)
```

> **No API keys?** The system operates in **mock mode** — fixed JSON responses are returned. The complete pipeline still works for development and testing.

### 3. Initialize the database

```bash
# Creates the 19 SQLite tables
python -c "
from persistence.base import build_engine, create_all_tables
create_all_tables(build_engine())
print('Database initialized.')
"

# Or via Alembic (recommended for production)
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access:

* **API**: [http://localhost:8000](http://localhost:8000)
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Docker

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Start API + Frontend
docker compose up -d --build

# Check status
docker compose ps
docker compose logs -f api
```

Services:

* **API**: [http://localhost:8000](http://localhost:8000)
* **Frontend**: [http://localhost:3000](http://localhost:3000)

---

## Tests

```bash
# Full suite (60 tests)
ANTHROPIC_API_KEY=mock OPENAI_API_KEY=mock \
python -m pytest tests/ -v

# By layer
python -m pytest tests/unit/        # domain invariants
python -m pytest tests/integration/ # elicitation pipeline
python -m pytest tests/api/         # HTTP endpoints

# With coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

---

## API Endpoints

| Method  | Endpoint                                         | Description                 |
| ------- | ------------------------------------------------ | --------------------------- |
| `GET`   | `/health`                                        | Health check                |
| `POST`  | `/api/v1/requirements/projects`                  | Create project              |
| `POST`  | `/api/v1/requirements/projects/{id}/elicit`      | Elicit requirements via LLM |
| `PATCH` | `/api/v1/requirements/{id}/refine`               | Refine requirement          |
| `POST`  | `/api/v1/requirements/{id}/approve`              | Approve requirement         |
| `POST`  | `/api/v1/requirements/projects/{id}/approve-all` | Bulk approval               |
| `GET`   | `/api/v1/requirements/projects/{id}`             | List project requirements   |

### Usage Example

```bash
# 1. Create project
curl -X POST http://localhost:8000/api/v1/requirements/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Banking System", "domain": "financial"}'

# 2. Elicit requirements from free-form text
curl -X POST http://localhost:8000/api/v1/requirements/projects/{project_id}/elicit \
  -H "Content-Type: application/json" \
  -d '{
    "raw_input": "The user must log in using CPF and password. After 3 incorrect attempts, the account must be locked for 30 minutes.",
    "language": "en"
  }'

# 3. Approve requirement
curl -X POST http://localhost:8000/api/v1/requirements/{req_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "tech-lead"}'
```

---

## Project Structure

```text
aqua-qe/
├── main.py                    # FastAPI entry point
├── persistence/base.py        # SQLAlchemy engine, session, declarative Base
├── shared/
│   ├── event_bus.py           # IEventBus + InProcessEventBus
│   └── wiring.py              # Dependency container (all contexts)
│
├── requirements/              # Upstream context — source of truth
│   ├── contracts/             # RequirementSnapshot, IRequirementReader, events
│   ├── domain/                # Entities, value objects (QualityScore, RequirementVersion)
│   ├── application/           # CreateRequirement, RefineRequirement, ApproveRequirement
│   └── infrastructure/        # SQLAlchemy models, Repository, Reader, Mappers
│
├── validation/                # Semantic validation + heuristics
├── testing/                   # Generates BDD using formal techniques
├── traceability/              # Bidirectional traceability (BFS)
├── accessibility/             # WCAG 2.1/2.2 + Nielsen heuristics
├── quality/                   # Quality gate — aggregates all contexts
├── knowledge/                 # Organizational memory + ACL
├── ai_gateway/                # Claude + OpenAI + router + fallback + ACL
│
├── api/requirements/          # FastAPI router + Pydantic schemas
├── tests/
│   ├── unit/                  # Pure domain (no I/O)
│   ├── integration/           # Full pipeline
│   └── api/                   # HTTP contracts
│
├── migrations/                # Alembic env.py + versions/
├── Dockerfile.api
├── Dockerfile.frontend
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## Make Commands

```bash
make dev          # Starts API with reload
make test         # Full suite
make test-unit    # Unit tests only
make test-int     # Integration tests only
make test-api     # HTTP API tests only
make lint         # Ruff check
make db-upgrade   # Apply migrations
make db-migrate MSG="desc"  # Generate new migration
make db-reset     # Reset database (dev)
make docker       # Start via docker compose
make docker-down  # Stop containers
make docker-logs  # Follow logs
make clean        # Remove cache
```

---

## Advanced Configuration

### Full Environment Variables

| Variable              | Default                  | Description                                                     |
| --------------------- | ------------------------ | --------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`   | —                        | Claude API key (preferred for extraction/validation/generation) |
| `OPENAI_API_KEY`      | —                        | OpenAI API key (automatic fallback + scoring)                   |
| `DATABASE_URL`        | `sqlite:///./aqua_qe.db` | Database URL (SQLite in MVP)                                    |
| `LOG_LEVEL`           | `INFO`                   | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)                 |
| `CORS_ORIGINS`        | `*`                      | Allowed frontend origins                                        |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`  | API URL accessible by browser                                   |
| `ENV`                 | `production`             | Environment (`development`, `production`)                       |

### LLM Routing

The AI Gateway automatically routes by operation type:

| Operation              | Default Provider | Fallback |
| ---------------------- | ---------------- | -------- |
| Requirement extraction | Claude           | OpenAI   |
| Semantic validation    | Claude           | OpenAI   |
| BDD test generation    | Claude           | OpenAI   |
| Quality scoring        | OpenAI           | Claude   |
| WCAG analysis          | Claude           | OpenAI   |

If no provider is available, the system returns structured mock responses.

### PostgreSQL Migration (Phase 2+)

```env
DATABASE_URL=postgresql+psycopg2://aquaqe:password@localhost:5432/aquaqe
```

No code changes are required — the persistence layer is abstracted through repositories.

---

## Contributing

### Adding a New Bounded Context

1. Create the structure `new_context/{contracts.py, domain/, application/, infrastructure/}`
2. Implement `contracts.py` with DTOs, service interfaces, and domain events
3. Create SQLAlchemy model with table prefix (`nvc_`)
4. Register model in `persistence/base.py` → `create_all_tables()`
5. Register model in `migrations/env.py`
6. Generate migration: `make db-migrate MSG="add_new_context"`
7. Register handlers in `shared/wiring.py`
8. Add tests in `tests/unit/` and `tests/integration/`

### Architecture Principles

* **No cross-domain imports**: contexts communicate only through contracts (`contracts.py`), domain events, or interfaces
* **ACL is mandatory** for `knowledge/` and `ai_gateway/` — never called directly
* **Repository is the only class** with database access in each context
* **Domain entities are POPOs** (Plain Old Python Objects) — no SQLAlchemy imports
* **Handlers are functions**, not classes — returned by factories that capture dependencies via closures

---

## License

MIT — see `LICENSE` for details.
