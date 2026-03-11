# TouchCLI — Conversational AI Sales Assistant

> No buttons. No forms. No dashboards. Just conversation and voice. A fleet of AI Agents works behind the scenes so sales reps never have to touch a UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/billbai-longarena/touchcli/actions/workflows/ci.yml/badge.svg)](https://github.com/billbai-longarena/touchcli/actions)

[中文文档](DESIGN.md)

---

## Overview

TouchCLI is a **pure conversational AI sales assistant framework** built for both B2B account managers and B2C consultants. Users speak or type; the Agent cluster automatically handles data entry, customer follow-ups, deal management, and strategic recommendations.

### Design Principles

| # | Principle | Meaning |
|---|-----------|---------|
| 1 | **Zero learning curve** | If you can talk, you can use it — no menus, no navigation, no "feature discovery" |
| 2 | **Agents act first** | Proactively push tasks and alerts without waiting for the user to ask |
| 3 | **Conversation is operation** | "Create a $500k deal for Zhang" creates the deal directly — no form redirect |
| 4 | **Voice-first** | Usable while driving, walking, or in a client meeting |
| 5 | **Consistent across devices** | Phone, tablet, desktop — same conversation flow, same experience |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + WebSocket |
| API Gateway | Go (Gin) |
| Backend | Python 3.11 + FastAPI + SQLAlchemy |
| Database | PostgreSQL 15 + Alembic migrations |
| Cache / Queue | Redis 7 + Celery |
| AI Framework | LangGraph + OpenAI |
| Containers | Docker + docker-compose + Kubernetes |

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & docker-compose (recommended)

### 1. Clone

```bash
git clone https://github.com/billbai-longarena/touchcli.git
cd touchcli
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY and other required values
```

### 3. Start with Docker (recommended)

```bash
docker-compose up -d
```

### 4. Start manually (development mode)

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
cd backend/python && pip install -r requirements.txt && cd ../..

# Run database migrations
./scripts/migrate-db.sh

# Terminal 1: Frontend
npm run dev

# Terminal 2: Python backend
cd backend/python && uvicorn main:app --reload

# Terminal 3: Go gateway
cd backend/go && go run main.go
```

### 5. Access the app

- Frontend: http://localhost:3000
- API docs: http://localhost:8080/docs

---

## Project Structure

```
touchcli/
├── frontend/          # React frontend (Vite + TypeScript)
├── backend/
│   ├── python/        # FastAPI business backend
│   └── go/            # Go API gateway
├── db/                # Migrations and seed data
├── k8s/               # Kubernetes manifests
├── scripts/           # Automation scripts (incl. Termite Protocol infrastructure)
├── signals/           # Termite Protocol signal store
├── docs/              # Supplementary docs
├── .env.example       # Environment variable template
├── docker-compose.yml # Local full-stack orchestration
└── openapi.yaml       # API specification
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [DESIGN.md](DESIGN.md) | Product vision, user scenarios, architecture, Agent topology (中文) |
| [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) | Full developer onboarding guide |
| [ENVIRONMENT_CONFIGURATION.md](ENVIRONMENT_CONFIGURATION.md) | All environment variables explained |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment architecture and runbooks |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture deep-dive |
| [openapi.yaml](openapi.yaml) | Full REST API specification |

---

## Termite Protocol

This project embeds the **Termite Protocol** — a multi-Agent concurrent collaboration framework that drives continuous project evolution.

- Specification: [TERMITE_PROTOCOL.md](TERMITE_PROTOCOL.md)
- Quick start: [QUICKSTART.md](QUICKSTART.md)
- Heartbeat kernel: [AGENTS.md](AGENTS.md)

---

## Contributing

Issues and Pull Requests are welcome. Please read [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) first to set up your local environment.

1. Fork this repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

[MIT](LICENSE) © 2026 billbai-longarena
