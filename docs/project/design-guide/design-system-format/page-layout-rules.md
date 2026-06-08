Doc ID: DESIGN-LAYOUT-001
Status: active
Source of truth: yes
Owner: design
Related docs: ui-design-direction.md, colors.md, ../pages-map.md
Update together with: ../pages-map.md, components-guidelines.md
Update trigger: изменение shell или grid
Review required: design
Maturity: L2

# Page Layout Rules

## Dashboard Shell

```text
+--------+-------------------------------------------+----------+
|Z-SIDEBAR| Z-MAIN-COLUMN                            |Z-INSIGHT |
| logo   | Z-TOPBAR: title, search, notify, CTA     | optional |
| nav    +-------------------------------------------+          |
| workspace| Z-CONTENT-GRID                          | widgets  |
| settings|  top: KPI | KPI | alert                 |          |
| logout |  mid: chart | AI insight                 |          |
|        |  bot: table | status                      |          |
+--------+-------------------------------------------+----------+
```

## Zones

| Zone | Description |
|---|---|
| Z-SIDEBAR | 260px, `--bg-sidebar`, subtle border |
| Z-TOPBAR | breadcrumbs/title, global search, profile, **one** primary CTA |
| Z-CONTENT-GRID | 3-row dashboard grid inside main |
| Z-INSIGHT | 320px optional right panel |

## Dashboard Grid (PAGE-002)

| Row | Zones |
|---|---|
| Top | Z-KPI-HERO · Z-KPI-SECONDARY · Z-ALERT-ACTION |
| Middle | Z-TREND-CHART · Z-AI-RECOMMENDATION |
| Bottom | Z-EMPLOYEE-TABLE · Z-SOURCES-STATUS |

## Sidebar Nav → Page ID

| RU | Page |
|---|---|
| Дашборд | PAGE-002 |
| Клиенты к разбору | PAGE-003 |
| История разборов | PAGE-004 |
| AI-аналитика | PAGE-005 |
| AI-агент | PAGE-007 |
| Настройки | PAGE-006 |

Active: contour border `--accent-contour`, subtle cyan bg — not filled pill.

## Responsive

≥1440: full 3-column · 1280: hide Z-INSIGHT to drawer · 1024: icon sidebar
