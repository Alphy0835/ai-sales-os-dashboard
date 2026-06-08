Doc ID: DESIGN-PREVIEW-PAGE-004
Page ID: PAGE-004
Shell: SHELL-MANAGER
Status: draft preview
Related docs: ../pages-map.md, PAGE-004-review-history.html

# Review History — PAGE-004

История проведённых разборов с сотрудниками.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | навигация менеджера | nav pills |
| Z-PAGE-HEADER | заголовок | title, subtitle |
| Z-FILTERS | фильтры | subdivision, employee |
| Z-REVIEWS-TABLE | таблица разборов | date, employee, comment, tasks |
| Z-REVIEW-FORM | создание/редактирование | modal (edit only) |
| Z-TASK-LIST | задачи в записи | checklist |

## ASCII Wireframe

```
+-------------+----------------------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: История разборов  |
| *Reviews    | Z-FILTERS: [sub] [employee]      |
|             | Z-REVIEWS-TABLE                  |
|             |  date | employee | comment | ... |
+-------------+----------------------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Active nav «История разборов»
- [ ] Filter row above table
- [ ] Sample rows with comments and task counts
- [ ] Primary CTA for new review
