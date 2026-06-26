# Agentic Commerce

AI-powered e-commerce backend with a conversational shopping assistant. Built with FastAPI, Next.js, SQLAlchemy, and LangChain.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | Next.js, React, Tailwind CSS, Radix UI |
| AI Agent | LangChain, LangGraph, Ollama (Gemma 4) |
| Search | Typesense (optional — SQL ILIKE fallback) |
| Payments | Razorpay |
| Auth | JWT (bcrypt), Google OAuth |
| Database | SQLite (dev), PostgreSQL-ready via SQLAlchemy |
| Tests | pytest (backends), Vitest + Playwright (frontend) |

## Prerequisites

- **Python 3.12+** and `uv` (package manager)
- **Node.js 20+** and `npm`
- **Ollama** with `gemma4` model pulled — `ollama pull gemma4`
- **Typesense 27+** (optional — search falls back to SQL ILIKE if disabled)

## Quick Start

### 1. Backend

```bash
cd backend
uv sync                   # Install dependencies
cp .env.example .env      # Configure environment (edit as needed)
uv run python main.py     # Start server at http://localhost:8000
```

The server auto-creates tables, seeds `admin@admin.com` / `test@test.com` users, and indexes Typesense on first startup.

### 2. Frontend

```bash
cd frontend
npm install               # Install dependencies
cp .env.example .env.local # Configure environment
npm run dev               # Start dev server at http://localhost:3000
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `sqlite:///./sqlite.db` | SQLAlchemy database URL |
| `SECRET_KEY` | **Yes** | — | JWT signing key (must be set) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `BACKEND_CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins |
| `GOOGLE_CLIENT_ID` | No | — | Google OAuth client ID |
| `RAZORPAY_KEY_ID` | No | — | Razorpay API key ID |
| `RAZORPAY_KEY_SECRET` | No | — | Razorpay API key secret |
| `RAZORPAY_WEBHOOK_SECRET` | No | — | Webhook signing secret |
| `SMTP_HOST` | No | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | No | — | SMTP username |
| `SMTP_PASSWORD` | No | — | SMTP password or App Password |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend URL for email links |
| `RATE_LIMIT` | No | `30` | Auth endpoint rate limit (req/min) |
| `TYPESENSE_ENABLED` | No | `false` | Enable Typesense search |
| `TYPESENSE_HOST` | No | `localhost` | Typesense host |
| `TYPESENSE_PORT` | No | `8108` | Typesense port |
| `TYPESENSE_PROTOCOL` | No | `http` | Typesense protocol |
| `TYPESENSE_API_KEY` | No | — | Typesense API key |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000/api/v1` | Backend API URL |
| `NEXT_PUBLIC_RAZORPAY_KEY_ID` | No | — | Razorpay key for checkout |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | No | — | Google OAuth client ID |

## AI Shopping Agent

The conversational agent runs locally via Ollama:

```bash
ollama pull gemma4        # Download the model (once)
```

The agent supports:
- **Product search** with sort/filter (price, rating, stock, discount, etc.)
- **Cart management** by product name (add, update, remove, clear)
- **Product details** and category browsing
- **Structured conversation state** — remembers last query, filters, sort, and results
- **Intent-based tool filtering** — only relevant tools exposed per turn

Chat endpoint: `POST /api/v1/chat` (authenticated)

## Typesense Search (Optional)

Typesense enables fast, typo-tolerant full-text search with infix matching.

```bash
# Start Typesense (Docker)
docker run -d -p 8108:8108 \
  -v /tmp/typesense-data:/data \
  typesense/typesense:27.0 \
  --data-dir /data \
  --api-key=your-api-key \
  --listen-port 8108

# Or use a local install on port 8108

# Set in .env:
TYPESENSE_ENABLED=true
TYPESENSE_API_KEY="your-api-key"
```

The server auto-indexes all products on startup. To manually reindex:

```bash
cd backend
uv run scripts/reindex_typesense.py
```

## Testing

### Backend (pytest)

```bash
cd backend
uv run pytest                   # All tests
uv run pytest -x                # Stop on first failure
uv run pytest tests/test_ai_tools.py  # AI agent tests
uv run pytest -n auto           # Parallel execution
uv run python tests/e2e_chat.py # E2E conversation test
```

### Frontend (Vitest + Playwright)

```bash
cd frontend
npm test                        # Vitest unit tests
npm run test:e2e               # Playwright E2E tests
```

## Project Structure

```
agentic-commerce/
├── backend/
│   ├── app/
│   │   ├── ai/                 # AI agent (agent, tools, prompts, intent, conversation)
│   │   ├── api/v1/endpoints/   # Route handlers (auth, products, cart, orders, chat, etc.)
│   │   ├── core/               # Config, security, exceptions, rate limiter
│   │   ├── db/                 # SQLAlchemy engine, session, base
│   │   ├── models/             # ORM models (product, user, cart, order, etc.)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic (product, cart, order, typesense, etc.)
│   ├── scripts/                # Utility scripts (seed, reindex typesense)
│   ├── tests/                  # pytest test suites (21 test files)
│   ├── alembic/                # Database migrations
│   └── data/                   # Seed data (products.json)
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js pages (products, cart, checkout, orders, admin, etc.)
│   │   ├── components/         # UI components (admin, features, shared)
│   │   ├── lib/                # API client, auth, utilities
│   │   ├── stores/             # Zustand state stores
│   │   └── types/              # TypeScript type definitions
│   └── tests/                  # Vitest unit + Playwright E2E tests
└── README.md
```

## API Documentation

With the server running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
