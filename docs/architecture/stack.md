Doc ID: ARCH-STACK-001
Status: active
Source of truth: yes
Owner: architecture
Related docs: docs/architecture/system-overview.md, docs/architecture/architecture-decisions/ADR-0001-django-nextjs-monorepo.md, docs/architecture/integrations.md
Update trigger: изменение версии или замена компонента стека
Maturity: L2

# Technology Stack — Confirmed

**Decision:** Variant A (2026-06-09). Solo fullstack, SaaS multi-tenant.

| Component | Choice | Status |
|---|---|---|
| Database | PostgreSQL 16 + **pgvector** | **Active** on PostgreSQL prod — `VectorField` on `KnowledgeArticle`, Celery embed task, vector search with keyword fallback. SQLite dev: keyword search only |
| Backend | Django 5 + DRF + drf-spectacular | Active |
| Frontend | Next.js 15 + TypeScript + Tailwind | Active |
| Queue | Celery + Redis 7 | Active |
| Auth | JWT (User Level) + Django Admin session (Integration) | Active — httpOnly JWT cookies (secure, SameSite=Lax); browser `localStorage` caches profile/permissions only |
| Multi-tenant | `tenant_id` column on rows | Active — filtered in **views/services**, not custom ORM managers |
| Object storage | ~~S3-compatible~~ | **Not used by design** — audio not persisted; transcripts in PostgreSQL only |
| AI / LLM | Adapter → **OpenRouter** (vendor-pluggable) | **Active** — `llm_adapter.py`; tenant/workspace keys in Admin; rule-based fallback without key |
| Speech-to-text (ASR) | OpenRouter STT (`stt_adapter`) | **Implemented** — transient audio on upload; demo fallback without API key |
| **Not in MVP start** | FastAPI | Revisit STAGE-006+ if needed |

## Implementation notes

- **Embeddings:** Celery task embeds KB articles; pgvector similarity search in `ai/services/knowledge.py` (PostgreSQL required for vectors).
- **LLM:** OpenRouter-compatible HTTP API — not a hard dependency on OpenAI brand; keys managed per tenant/workspace.
- **Media:** No S3 bucket in compose or settings; `integrations` validates uploads but does not persist audio files.
- **Retention:** 90-day transcript purge via Celery (`integrations.purge_expired_transcripts`).

Implementation: [system-overview.md](system-overview.md) · Rationale: [ADR-0001](architecture-decisions/ADR-0001-django-nextjs-monorepo.md) · Integrations: [integrations.md](integrations.md)
