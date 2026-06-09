Doc ID: ROADMAP-STAGE-004
Status: active
Source of truth: yes
Owner: fullstack
Related docs: docs/project/roadmap.md, docs/features/review-cycle/review-cycle.md
Update trigger: review API or PAGE-004/008 UI change
Review required: product, frontend, QA

# STAGE-004 — Review Cycle (Implementation)

**Completed:** 2026-06-09

## Summary

Review history (PAGE-004), task creation by managers, employee task list on personal dashboard (PAGE-008), task status sync back to history. Audit on review create.

## Backend

| Area | Path |
|---|---|
| App | `apps/api/reviews/` |
| Models | `Review`, `ReviewTask` |
| Manager API | `GET/POST /api/v1/manager/reviews/` |
| Employee API | `PATCH /api/v1/employee/tasks/{id}/` |
| Employee dashboard | `GET /api/v1/employee/dashboard/` includes `tasks` |
| Audit | `AuditLog.Action.REVIEW_CREATE` |
| Seed | `python manage.py seed_reviews` (via `seed_demo`) |
| Tests | `reviews/tests/test_stage004.py` |

## Frontend

| Page | Route | Component |
|---|---|---|
| PAGE-004 | `/manager/reviews` | `ReviewHistory.tsx` |
| PAGE-008 | `/employee` | `EmployeeDashboard.tsx` (tasks section) |

## Features covered

- REQ-005: review history, filters, create with tasks, task status in history
- REQ-006: employee metrics + manager tasks on personal dashboard

## Not in this slice

- Review edit/delete after creation
- AI-generated tasks (STAGE-005+)
- Employee agent page (STAGE-006)

## QA

`python manage.py test reviews.tests` · FLOW-002 / FLOW-006 manual · `npm run build`

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [review-cycle.md](../features/review-cycle/review-cycle.md)
