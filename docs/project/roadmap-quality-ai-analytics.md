Doc ID: ROADMAP-STAGE-005
Status: active
Source of truth: yes
Owner: fullstack
Related docs: docs/project/roadmap.md, docs/features/quality-ai-analytics/quality-ai-analytics.md
Update trigger: criteria API, report generation, PAGE-005/006 UI change
Review required: product, backend, QA

# STAGE-005 — Quality & AI Analytics (Implementation)

**Completed:** 2026-06-09

## Summary

Quality criteria configuration (PAGE-006 settings section) and rule-based AI analytics reports with canvas (PAGE-005). MVP uses keyword matching on transcriptions; full LLM scoring — post-MVP.

## Backend

| Area | Path |
|---|---|
| App | `apps/api/ai/` |
| Models | `QualityCriterion`, `AnalyticsReport` |
| Criteria API | `GET/POST /api/v1/manager/settings/quality-criteria/` |
| Criteria detail | `PATCH/DELETE .../quality-criteria/{id}/` |
| Reports | `GET /api/v1/manager/analytics/reports/` |
| Run report | `POST /api/v1/manager/analytics/reports/run/` |
| Seed | `python manage.py seed_ai` (via `seed_demo`) |
| Tests | `ai/tests/test_stage005.py` |

## Frontend

| Page | Route | Component |
|---|---|---|
| PAGE-005 | `/manager/analytics` | `AiAnalytics.tsx` |
| PAGE-006 (criteria) | `/manager/settings` | `QualityCriteriaSettings.tsx` |

## Features covered

- REQ-007: standard report templates, canvas (stages, recommendations → review)
- REQ-008: criteria CRUD with settings view/edit permissions

## Not in this slice

- Real OpenAI/LLM scoring (uses keyword rules on demo transcripts)
- Custom reports (STAGE-007)
- Full settings hub (permissions UI — optional follow-up)

## QA

`python manage.py test ai.tests` · FLOW-003 manual · `npm run build`

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [quality-ai-analytics.md](../features/quality-ai-analytics/quality-ai-analytics.md)
