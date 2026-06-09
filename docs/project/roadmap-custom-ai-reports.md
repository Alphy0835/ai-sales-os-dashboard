Doc ID: ROADMAP-STAGE-007
Status: active
Source of truth: yes
Owner: fullstack
Related docs: docs/project/roadmap.md, docs/features/custom-ai-reports/custom-ai-reports.md
Update trigger: custom report API, structuring rules, PAGE-005/006 UI change
Review required: product, AI, QA

# STAGE-007 — Custom AI Reports (Implementation)

**Completed:** 2026-06-09

## Summary

Managers describe custom analytics reports in natural language; the system structures the description into a query, saves it, and allows re-run from AI Analytics with stage-focused criteria filtering.

## Backend

| Area | Path |
|---|---|
| App | `apps/api/ai/` (extended) |
| Models | `CustomReport`, `AnalyticsReport.custom_report`, `AnalyticsReport.Template.CUSTOM` |
| Structuring | `ai/services/custom_reports.py` — rule-based MVP (`focus_stages`, `focus_keywords`) |
| Custom reports API | `GET/POST /api/v1/manager/settings/custom-reports/` |
| Detail API | `GET/PATCH/DELETE .../custom-reports/{id}/` |
| Run integration | `POST /api/v1/manager/analytics/reports/run/` — optional `custom_report_id` |
| Seed | `python manage.py seed_custom_reports` |
| Tests | `ai/tests/test_stage007.py` |

## Frontend

| Page | Route | Component |
|---|---|---|
| PAGE-006 (custom reports tab) | `/manager/settings` | `CustomReportsSettings.tsx` |
| PAGE-005 | `/manager/analytics` | `AiAnalytics.tsx` — custom report picker in template select |

## Features covered

- REQ-009: natural-language custom report description, save, re-run from AI analytics

## Not in this slice

- LLM-based prompt structuring
- Custom report sharing across tenants
- Visual query builder

## QA

`python manage.py test ai.tests.test_stage007` · FLOW-004 manual

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [custom-ai-reports.md](../features/custom-ai-reports/custom-ai-reports.md)
