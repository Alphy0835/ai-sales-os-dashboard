Doc ID: FRONTEND-DOCS-001
Status: active
Source of truth: yes
Owner: frontend
Related docs: docs/project/design-guide/pages-map.md, docs/project/design-guide/design-system-format/ui-kit.md, docs/architecture/api-contracts.md, docs/project/user-flow.md
Update together with: pages-map.md, api-contracts.md, components-guidelines.md
Update trigger: новая страница, route, компонент или изменение API usage
Review required: frontend, design
Maturity: L2

# Frontend Docs

## Purpose

Next.js App Router app (`apps/web`) — User Level UI. Визуал из [design-system-preview](../project/design-guide/design-system-preview/design-system-preview.md); PAGE-002 — эталон tokens/components.

Backend — только JSON via [api-contracts.md](../architecture/api-contracts.md).

## Frontend Scope

| Area | Included | Notes | Related Docs |
|---|---|---|---|
| Pages / routes | yes | Match pages-map routes | pages-map.md |
| Components | yes | Shell, Card, forms, tables | ui-kit.md, components-guidelines.md |
| State management | yes | React state + API client; auth in memory/cookie | — |
| API usage | yes | fetch to `NEXT_PUBLIC_API_URL` | api-contracts.md |
| Auth states | yes | guest, authenticated, forbidden, session expired | STAGE-001 |
| Design tokens | yes | CSS variables / Tailwind theme from preview-base.css | colors.md |

## Pages / Routes

Source of truth for Page ID: [pages-map.md](../project/design-guide/pages-map.md).

| Page ID | Route | Next.js path | Shell | Role | Status |
|---|---|---|---|---|---|
| PAGE-001 | `/login` | `app/login/page.tsx` | SHELL-AUTH | all | **implemented** |
| PAGE-002 | `/manager` | `app/manager/page.tsx` | SHELL-MANAGER | Manager | **implemented** |
| PAGE-003 | `/manager/clients` | `app/manager/clients/page.tsx` | SHELL-MANAGER | Manager | **implemented** |
| PAGE-004 | `/manager/reviews` | `app/manager/reviews/page.tsx` | SHELL-MANAGER | Manager | planned |
| PAGE-005 | `/manager/analytics` | `app/manager/analytics/page.tsx` | SHELL-MANAGER | Manager | planned |
| PAGE-006 | `/manager/settings` | `app/manager/settings/page.tsx` | SHELL-MANAGER | Manager | planned |
| PAGE-007 | `/manager/agent` | `app/manager/agent/page.tsx` | SHELL-MANAGER | Manager | planned |
| PAGE-008 | `/employee` | `app/employee/page.tsx` | SHELL-EMPLOYEE | Employee | **implemented** (metrics stub) |
| PAGE-009 | `/employee/agent` | `app/employee/agent/page.tsx` | SHELL-EMPLOYEE | Employee | planned |

Post-login redirect: `manager` → `/manager`, `employee` → `/employee` (from `/api/v1/auth/me/`).

## Components

| Component | Purpose | Used on | Design ref |
|---|---|---|---|
| `AmbientBackground` | App background + texture | all shells | preview `.ambient` |
| `AuthLayout` | Centered login card | PAGE-001 | SHELL-AUTH |
| `ManagerShell` | Sidebar + main + optional insight | PAGE-002–007 | SHELL-MANAGER |
| `EmployeeShell` | Sidebar + main | PAGE-008–009 | SHELL-EMPLOYEE |
| `Card`, `Button`, `Input` | UI kit primitives | all | ui-kit.md |
| `SidebarNav` | Nav items + active state | shells | pages-map nav |

Assets: `/bacground.png` copied from design-system-preview.

## State Management

| State area | Source | Persistence |
|---|---|---|
| Auth tokens | login API response | `localStorage` (MVP) |
| Current user / role | `GET /api/v1/auth/me/` | memory + refetch on load |
| Page data | REST endpoints | server state per page |

## API Usage

Base URL: `process.env.NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

| Action | Method | Path |
|---|---|---|
| Login | POST | `/api/v1/auth/login/` |
| Refresh | POST | `/api/v1/auth/refresh/` |
| Current user | GET | `/api/v1/auth/me/` |
| Manager dashboard | GET | `/api/v1/manager/dashboard/` |
| Clients to review | GET | `/api/v1/manager/clients/` |
| Employee dashboard | GET | `/api/v1/employee/dashboard/` |
| Metrics (raw) | GET | `/api/v1/integrations/metrics/` |

Authorization header: `Bearer {access_token}`.

## Auth States

| State | UI behavior |
|---|---|
| guest | Only `/login`; redirect from protected routes |
| authenticated | Shell by role; wrong role → forbidden page |
| session expired | Clear tokens → `/login` |
| forbidden | Message + link back to home route |

## Repository Layout

```
apps/web/
├── src/
│   ├── app/              # routes (pages-map)
│   ├── components/       # shell, ui
│   ├── lib/              # api client, auth
│   └── styles/           # globals, tokens
├── public/bacground.png
└── package.json
```

## Local Development

```bash
cd apps/web && npm install
npm run dev   # http://localhost:3000
```

Requires API at `http://localhost:8000`. See [environments.md](../operations/environments.md).

## Related Docs

- [backend-docs.md](../backend/backend-docs.md)
- [design-system-preview.md](../project/design-guide/design-system-preview/design-system-preview.md)
