Doc ID: DESIGN-PREVIEW-PAGE-002
Page ID: PAGE-002
Shell: SHELL-MANAGER
Status: review (v1 baseline — visual polish → v2, см. `../visual-iteration.md`)
Source of truth: yes
Owner: design
Related docs: ../pages-map.md, ../design-system-format/ui-kit.md, ../design-system-format/colors.md, ../design-system-format/page-layout-rules.md, ../design-system-format/components-guidelines.md, docs/project/user-flow.md (FLOW-001)
Update together with: PAGE-002-manager-dashboard.html, ../pages-map.md
Update trigger: изменение зон, контента или layout PAGE-002
Review required: design, product
Maturity: L1

# Manager Dashboard — PAGE-002

Preview-спека главного дашборда руководителя. HTML: `PAGE-002-manager-dashboard.html`.

> Flow: FLOW-001  
> Feature: FEAT-003  
> Route: `/manager`

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | навигация, workspace | logo, nav items, subdivision select, settings, logout |
| Z-PAGE-HEADER | заголовок экрана | H1, subtitle, breadcrumb scope |
| Z-TOOLBAR | фильтры и CTA | period chips, subdivision/employee selects, «Клиенты к разбору» link |
| Z-KPI-TODAY | KPI за сегодня | 4× metric card |
| Z-KPI-PERIOD | сводка периода | 2× metric card + delta |
| Z-TREND | динамика | line chart placeholder, norm line |
| Z-DRILLDOWN | детализация | selects: подразделение → сотрудник |
| Z-QUICK-LINKS | быстрые действия | ghost buttons → PAGE-003, PAGE-004 |
| Z-INSIGHT | AI-сводка | ai-focus card: просадки, контроль, похвалить |

## ASCII Wireframe

```
+-----------------------------------------------------------------------------+
| SHELL-MANAGER — PAGE-002 Manager Dashboard                                  |
+----------+------------------------------------------------+-----------------+
|Z-SIDEBAR | Z-MAIN                                         | Z-INSIGHT       |
|          | Z-PAGE-HEADER                                  |                 |
| [Logo]   |  Дашборд подразделения                         | AI-сводка       |
| AI Sales |  Сводка по ОП · CRM + телефония                | (ai-focus)      |
| OS       +------------------------------------------------+                 |
|          | Z-TOOLBAR                                      | [!] Просадка    |
| *Dash    | [Сегодня][Неделя][Месяц]  [Подразделение v]    |  качества у     |
|  Clients | [Сотрудник v]  [Клиенты к разбору ->]          |  3 менеджеров   |
|  Reviews +------------------------------------------------+                 |
|  Analyt  | Z-KPI-TODAY                                    | [i] Контроль    |
|  Agent   | +--------+ +--------+ +--------+ +--------+   |  Иванов, Петров |
|  Settings| | Звонки | |Касания | |Качество| |  План  |   |                 |
|          | |  142   | |   89   | |  78%   | |  92%   |   | [+] Похвалить   |
|          | +--------+ +--------+ +--------+ +--------+   |  Сидорова       |
| [Отдел v]+------------------------------------------------+                 |
| Settings | Z-KPI-PERIOD + Z-TREND                       | [->] Подробнее  |
| Logout   | +------------------+ +---------------------+ |                 |
|          | | Неделя / Месяц   | | Динамика + норма    | |                 |
|          | +------------------+ | ~~~~ chart ~~~~     | |                 |
|          | Z-DRILLDOWN          +---------------------+ |                 |
|          | Z-QUICK-LINKS: [Разбор] [AI-аналитика]    |                 |
+----------+------------------------------------------------+-----------------+
```

## Mock Data (Preview)

Данные для HTML — иллюстративные, не контракт API.

| Block | Sample |
|---|---|
| Звонки сегодня | 142 (+8%) |
| Касания | 89 (-3%) |
| Качество | 78% |
| План | 92% |
| AI просадка | качество у 3 менеджеров |
| Контроль | Иванов, Петров |
| Похвалить | Сидорова |

## States

| State | Z-CONTENT behavior |
|---|---|
| loading | skeleton on KPI row + chart |
| empty | «Нет данных за период» + hint check integrations |
| partial | KPI visible + banner «Телефония недоступна» |
| error | retry on chart block |
| forbidden | replace Z-MAIN with access denied |

## Links

| Action | Target |
|---|---|
| Sidebar «Клиенты к разбору» | PAGE-003 |
| Toolbar «Клиенты к разбору» | PAGE-003 |
| «Провести разбор» | PAGE-004 |
| «AI-аналитика» | PAGE-005 |
| Insight «Подробнее» | PAGE-003 or PAGE-005 |

## Approval Checklist

- [ ] Shell: sidebar + main + insight соответствует `page-layout-rules.md`
- [ ] Glass style без glow на всех картах
- [ ] AI insight в Z-INSIGHT, не дублирует KPI
- [ ] Nav active только Dashboard
- [ ] Product/content OK for FLOW-001

## Related Docs

- `PAGE-002-manager-dashboard.html`
- `../pages-map.md`
- `../design-system-format/components-guidelines.md`
