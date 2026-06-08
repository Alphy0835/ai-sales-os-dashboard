Doc ID: DESIGN-PREVIEW-PAGE-008
Page ID: PAGE-008
Shell: SHELL-EMPLOYEE
Status: draft preview
Related docs: ../pages-map.md, PAGE-008-employee-dashboard.html

# Employee Dashboard — PAGE-008

Личный дашборд сотрудника: метрики, динамика и задачи.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | nav (2 items) | Dashboard, AI Agent |
| Z-PAGE-HEADER | заголовок | title |
| Z-KPI | личные метрики | metric cards |
| Z-TREND | динамика | chart block |
| Z-TASKS | задачи от руководителя | task list |

## ASCII Wireframe

```
+-------------+----------------------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: Дашборд           |
| *Dashboard  | Z-KPI: [metric][metric][metric]|
|   AI Agent  | Z-TREND: chart                   |
|   Logout    | Z-TASKS: task list               |
+-------------+----------------------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Employee shell with 2 nav items only
- [ ] KPI metric cards row
- [ ] Trend chart block
- [ ] Tasks from manager visible
