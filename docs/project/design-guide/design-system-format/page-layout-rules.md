Doc ID: DESIGN-LAYOUT-001
Status: draft
Source of truth: yes
Owner: design
Related docs: ui-kit.md, colors.md, ../pages-map.md, components-guidelines.md
Update together with: ui-kit.md, ../pages-map.md, components-guidelines.md
Update trigger: изменение shell, колонок, зон или breakpoints
Review required: design, frontend
Maturity: L1

# Page Layout Rules

Правила компоновки экранов AI Sales OS в формате **AI Control Dashboard**.

## Base Page Structure

### Dashboard Shell (Manager & Employee)

```text
+------------------------------------------------------------------+
|  [App viewport — bg-main + ambient gradients]                    |
|  +----------+--------------------------------+----------------+  |
|  | Z-SIDEBAR| Z-MAIN                         | Z-INSIGHT      |  |
|  | 240-280px| flex-1                         | 320-360px      |  |
|  |          |                                | (optional)     |  |
|  | Logo     | Z-PAGE-HEADER                  | AI summary     |  |
|  | Nav      | Z-TOOLBAR (filters, actions)   | Quick stats    |  |
|  | Workspace| Z-CONTENT (cards grid)         | Notes / alerts |  |
|  | Settings |                                |                |  |
|  | Logout   |                                |                |  |
|  +----------+--------------------------------+----------------+  |
+------------------------------------------------------------------+
```

### Auth Shell (Login)

Centered glass card on `--bg-main` + ambient gradient. Без sidebar. См. `../pages-map.md` → SHELL-AUTH.

## Zone Definitions

| Zone ID | Width | Description |
|---|---|---|
| Z-SIDEBAR | 260px fixed | glass panel, rounded outer corners (radius-xl) |
| Z-MAIN | flex 1, min 640px | primary work area |
| Z-INSIGHT | 340px | collapsible on `<1280px`; hidden on settings full-width |
| Z-PAGE-HEADER | full width of main | H1 + subtitle |
| Z-TOOLBAR | full width of main | filter chips, date range, primary CTA |
| Z-CONTENT | full width of main | grid of glass cards |

### Manager Sidebar Nav → Page ID

| Label (RU) | Page ID | Icon role |
|---|---|---|
| Дашборд | PAGE-002 | home / grid |
| Клиенты к разбору | PAGE-003 | users / alert |
| История разборов | PAGE-004 | list / checklist |
| AI-аналитика | PAGE-005 | chart |
| AI-агент | PAGE-007 | spark / chat |
| Настройки | PAGE-006 | gear |

Items hidden when permission = `none`. Active item: glow pill (`--accent-blue`).

### Employee Sidebar Nav

| Label (RU) | Page ID |
|---|---|
| Дашборд | PAGE-008 |
| AI-агент | PAGE-009 |

### Z-INSIGHT Usage by Page

| Page ID | Z-INSIGHT content |
|---|---|
| PAGE-002 | AI-сводка, кого контролировать, быстрые alerts |
| PAGE-003 | топ причин к разбору |
| PAGE-005 | preview метрик / last report |
| PAGE-006 | hidden (full-width settings) |
| PAGE-007 | context panel / RAG sources |
| PAGE-008 | tasks preview, plan delta |
| PAGE-009 | optional tips |

## Spacing

| Context | Padding / Gap |
|---|---|
| App outer | 24px |
| Sidebar inner | 20px vertical, 16px horizontal |
| Main padding | 32px |
| Between sections | 24px (space-lg) |
| Card grid gap | 16–24px |
| Page header → toolbar | 16px |
| Toolbar → content | 24px |

## Page Rules

1. **Hierarchy:** title → subtitle → toolbar → content grid → detail.
2. **One primary CTA** per screen in Z-TOOLBAR (e.g. «Новый разбор», «Запустить отчёт»).
3. **Cards grid:** 12-column logic — KPI row 3–4 cols; wide chart 8–12 cols.
4. **Glass nesting:** max 2 levels (panel → card); не вкладывать glass глубже.
5. **Insight panel:** secondary info only; critical actions stay in Z-MAIN.

## Responsive Design

| Breakpoint | Behavior |
|---|---|
| ≥1440px | sidebar + main + insight |
| 1280–1439px | insight collapses to drawer / bottom sheet |
| 1024–1279px | sidebar → icon rail (72px) + labels on hover |
| <1024px | out of scope MVP; show «desktop recommended» banner |

Preview HTML (MVP): desktop 1440px baseline.

## Related Docs

- `../pages-map.md`
- `ui-kit.md`
- `components-guidelines.md`
