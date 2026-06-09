# AI Sales OS — Monorepo

Product docs: [`docs/`](docs/) · Stack: [`docs/architecture/stack.md`](docs/architecture/stack.md)

## Apps

| Path | Stack | Role |
|---|---|---|
| [`apps/api`](apps/api) | Django 5 + DRF | REST API, Celery, Admin |
| [`apps/web`](apps/web) | Next.js 15 | User Level UI |

## Quick start (local)

**One command:**

| OS | Command |
|---|---|
| Windows | Double-click **`start-dev.bat`** or `.\start-dev.ps1` |
| macOS / Linux | `./start-dev.sh` (chmod +x once) |

If Docker is not installed, the launcher detects your OS and offers:

- **[I]** auto-install (Windows: `winget`, macOS: `brew`)
- **[D]** open download page
- **[R]** retry after starting Docker Desktop
- **[L]** continue in **LOCAL mode** (SQLite, no Postgres/Redis)

```powershell
# Windows options
.\start-dev.ps1 -InstallDocker     # try winget install without menu
.\start-dev.ps1 -NonInteractive    # skip menu, LOCAL if no Docker
.\start-dev.ps1 -RequireDocker     # fail unless Docker is ready
.\start-dev.ps1 -RunTests          # same as test.bat
.\start-dev.ps1 -DockerAll         # full stack in Docker (no local Python/Node)
```

```bash
# macOS / Linux options
./start-dev.sh --install-docker
./start-dev.sh --non-interactive
./start-dev.sh --run-tests
./start-dev.sh --docker-all
```

Starts Postgres + Redis when Docker is available; otherwise SQLite. Migrates, seeds demo data, opens API + Celery + Next.js.

| File | Action |
|---|---|
| `start-dev.bat` / `start-dev.ps1` | Windows full local stack |
| `start-dev.sh` | macOS / Linux full local stack |
| `test.bat` | API tests only (`-RunTests`, works without Docker) |
| `scripts/docker-setup.ps1` | Docker detect + install assist (Windows) |
| `scripts/docker-setup.sh` | Docker detect + install assist (Unix) |

Manual steps (if needed):

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

Implementation follows [`docs/project/roadmap.md`](docs/project/roadmap.md). **STAGE-001–006 done**. Next: **STAGE-007** Custom AI Reports.
