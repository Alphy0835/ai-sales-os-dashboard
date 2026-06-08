Doc ID: DESIGN-PREVIEW-INDEX-001
Status: draft
Source of truth: yes
Owner: design
Related docs: docs/project/design-guide/pages-map.md, docs/project/design-guide/work-rules-design-guide.md, docs/project/design-guide/design-system-preview/work-rules-design-system-preview.md
Update together with: pages-map.md, work-rules-design-guide.md
Update trigger: добавление или изменение preview-страницы, статуса или пути к файлам
Review required: design
Maturity: L1

# Design System Preview — Index

Индекс ASCII-спек и HTML-preview страниц User Level.

> Структура экранов: `../pages-map.md`  
> Правила preview: `work-rules-design-system-preview.md`

Source of truth для макета страницы — `.md` файл. HTML — визуализация по `.md` и `design-system-format/`.

## Preview Index

| Page ID | Page Name | Markdown Spec | HTML Preview | Shell | Status |
|---|---|---|---|---|---|
| PAGE-001 | Login | `PAGE-001-login.md` | `PAGE-001-login.html` | SHELL-AUTH | planned |
| PAGE-002 | Manager Dashboard | `PAGE-002-manager-dashboard.md` | `PAGE-002-manager-dashboard.html` | SHELL-MANAGER | review (v1) |

> Visual refresh v2: `../visual-iteration.md` · новые refs → `../references/v2/`
| PAGE-003 | Clients To Review | `PAGE-003-clients-to-review.md` | `PAGE-003-clients-to-review.html` | SHELL-MANAGER | planned |
| PAGE-004 | Review History | `PAGE-004-review-history.md` | `PAGE-004-review-history.html` | SHELL-MANAGER | planned |
| PAGE-005 | AI Analytics | `PAGE-005-ai-analytics.md` | `PAGE-005-ai-analytics.html` | SHELL-MANAGER | planned |
| PAGE-006 | System Settings | `PAGE-006-system-settings.md` | `PAGE-006-system-settings.html` | SHELL-MANAGER | planned |
| PAGE-007 | AI Agent (Manager) | `PAGE-007-ai-agent-manager.md` | `PAGE-007-ai-agent-manager.html` | SHELL-MANAGER | planned |
| PAGE-008 | Employee Dashboard | `PAGE-008-employee-dashboard.md` | `PAGE-008-employee-dashboard.html` | SHELL-EMPLOYEE | planned |
| PAGE-009 | AI Agent (Employee) | `PAGE-009-ai-agent-employee.md` | `PAGE-009-ai-agent-employee.html` | SHELL-EMPLOYEE | planned |

Все файлы располагаются в этой папке: `design-system-preview/`.

## MVP Priority

Порядок создания preview для первого релиза User Level:

1. PAGE-001 — Login  
2. PAGE-002 — Manager Dashboard  
3. PAGE-008 — Employee Dashboard  
4. PAGE-004 — Review History  
5. PAGE-003 — Clients To Review  
6. PAGE-005 — AI Analytics  
7. PAGE-006 — System Settings  
8. PAGE-007, PAGE-009 — AI Agents  

## File Pair Rule

- Каждая страница = пара `PAGE-xxx-slug.md` + `PAGE-xxx-slug.html`.
- HTML создаётся только после утверждения ASCII в `.md`.
- Изменение зон в `pages-map.md` → обновить `.md` → обновить `.html`.
