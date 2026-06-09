Doc ID: ROADMAP-STAGE-003
Status: active
Source of truth: yes
Owner: fullstack
Related docs: docs/project/roadmap.md, docs/features/manager-dashboard/manager-dashboard.md
Update trigger: dashboard API or PAGE-002/003 UI change
Review required: product, frontend, QA

# STAGE-003 — Manager Dashboard (Implementation)

**Completed:** 2026-06-09

## Summary

Manager dashboard (PAGE-002) and clients to review (PAGE-003) wired to integration metrics + rule-based AI summary. Employee personal dashboard stub.

## Backend

| Area | Path |
|---|---|
| App | `apps/api/analytics/` |
| Model | `ClientToReview` |
| Dashboard API | `GET /api/v1/manager/dashboard/` |
| Clients API | `GET /api/v1/manager/clients/` |
| Employee API | `GET /api/v1/employee/dashboard/` |
| Seed | `python manage.py seed_dashboard` |
| Tests | `analytics/tests/test_stage003.py` |

## Frontend

| Page | Route | Component |
|---|---|---|
| PAGE-002 | `/manager` | `ManagerDashboard.tsx` |
| PAGE-003 | `/manager/clients` | `ClientsToReview.tsx` |
| Employee | `/employee` | `EmployeeDashboard.tsx` |

## Features covered

- REQ-001: metrics today/week/month, trend, source status
- REQ-002: workspace + employee drill-down filters
- REQ-003: rule-based AI summary (full LLM — STAGE-005+)
- REQ-004: clients to review list

## Not in this slice

- Review creation (STAGE-004)
- Full AI analytics reports (STAGE-005)
- Stub manager pages: reviews, analytics, settings, agent

## QA

`python manage.py test analytics.tests.test_stage003` · `npm run build` in `apps/web`

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [manager-dashboard.md](../features/manager-dashboard/manager-dashboard.md)
