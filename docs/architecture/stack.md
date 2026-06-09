Doc ID: ARCH-STACK-001
Status: active
Source of truth: yes
Owner: architecture
Related docs: docs/architecture/system-overview.md, docs/architecture/architecture-decisions/ADR-0001-django-nextjs-monorepo.md
Update trigger: изменение версии или замена компонента стека
Maturity: L2

# Technology Stack — Confirmed

**Decision:** Variant A (2026-06-09). Solo fullstack, SaaS multi-tenant.

| Component | Choice |
|---|---|
| Database | PostgreSQL 16 + pgvector |
| Backend | Django 5 + DRF + drf-spectacular |
| Frontend | Next.js 15 + TypeScript + Tailwind |
| Queue | Celery + Redis 7 |
| Auth | JWT (User Level) + Django Admin session (Integration) |
| Multi-tenant | `tenant_id` column (MVP) |
| Storage | S3-compatible |
| AI | Adapter → OpenAI (vendor pluggable) |
| **Not in MVP start** | FastAPI (revisit STAGE-006+) |

Implementation: [system-overview.md](system-overview.md) · Rationale: [ADR-0001](architecture-decisions/ADR-0001-django-nextjs-monorepo.md)
