Doc ID: ROADMAP-STAGE-006
Status: active
Source of truth: yes
Owner: fullstack
Related docs: docs/project/roadmap.md, docs/features/knowledge-base-ai-agents/knowledge-base-ai-agents.md
Update trigger: knowledge API, agent chat, PAGE-006/007/009 UI change
Review required: product, AI, QA

# STAGE-006 — Knowledge Base & AI Agents (Implementation)

**Completed:** 2026-06-09

## Summary

Knowledge base CRUD in settings, rule-based RAG search, manager and employee AI agent chat with client context and access-level filtering.

## Backend

| Area | Path |
|---|---|
| App | `apps/api/ai/` (extended) |
| Models | `KnowledgeArticle`, `AgentChatSession`, `AgentChatMessage` |
| Knowledge API | `GET/POST /api/v1/manager/settings/knowledge/` |
| Agent API | `POST /api/v1/manager/agent/chat/`, `POST /api/v1/employee/agent/chat/` |
| Seed | `python manage.py seed_knowledge` |
| Tests | `ai/tests/test_stage006.py` |

## Frontend

| Page | Route | Component |
|---|---|---|
| PAGE-006 (KB tab) | `/manager/settings` | `KnowledgeBaseSettings.tsx` |
| PAGE-007 | `/manager/agent` | `AgentChat.tsx` |
| PAGE-009 | `/employee/agent` | `AgentChat.tsx` |

## Features covered

- REQ-010: knowledge base CRUD, RAG in agents
- REQ-011: manager agent with client context + sources
- REQ-012: employee agent with access restrictions message

## Not in this slice

- pgvector embeddings / OpenAI chat
- Per-article permission grants (REQ-013 UI) — uses access_level enum
- Deal success/failure ML training

## QA

`python manage.py test ai.tests.test_stage006` · FLOW-005 / FLOW-007 manual

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [knowledge-base-ai-agents.md](../features/knowledge-base-ai-agents/knowledge-base-ai-agents.md)
