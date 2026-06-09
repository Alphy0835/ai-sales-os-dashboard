# AI Sales OS — Monorepo

Product docs: [`docs/`](docs/) · Stack: [`docs/architecture/stack.md`](docs/architecture/stack.md)

## Apps

| Path | Stack | Role |
|---|---|---|
| [`apps/api`](apps/api) | Django 5 + DRF | REST API, Celery, Admin |
| [`apps/web`](apps/web) | Next.js 15 | User Level UI |

## Quick start (local)

```bash
cp .env.example .env

# Infrastructure
docker compose up -d postgres redis

# API
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver

# Web (new terminal)
cd apps/web
npm install
npm run dev
```

- Web: http://localhost:3000  
- API: http://localhost:8000/api/v1/health/  
- Demo: `manager@demo.local` / `demo1234` (top manager) · `regional@demo.local` · `employee@demo.local` · `employee-spb@demo.local`

## Docker (all services)

```bash
cp .env.example .env
docker compose up --build
```

## Roadmap

Implementation follows [`docs/project/roadmap.md`](docs/project/roadmap.md). **STAGE-001–002 done**. Next: **STAGE-003** Manager Dashboard.
