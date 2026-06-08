Doc ID: DESIGN-PREVIEW-PAGE-003
Page ID: PAGE-003
Shell: SHELL-MANAGER
Status: draft preview
Related docs: ../pages-map.md, PAGE-003-clients-to-review.html

# Clients To Review — PAGE-003

Список клиентов, требующих разбора с сотрудниками.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | навигация менеджера | nav pills, subdivision |
| Z-PAGE-HEADER | заголовок страницы | title, subtitle |
| Z-FILTERS | фильтры списка | subdivision, employee, status |
| Z-CLIENT-LIST | таблица клиентов | client, employee, reason |
| Z-ROW-ACTIONS | действия строки | разбор, AI |
| Z-INSIGHT | AI-сводка | optional quick stats |

## ASCII Wireframe

```
+-------------+----------------------------------+------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: Клиенты к разбору| Z-INSIGHT        |
| *Clients    | Z-FILTERS: [sub] [emp] [status] | 3 в очереди      |
|   Dashboard | Z-CLIENT-LIST                    | AI hint          |
|   ...       |  table + Z-ROW-ACTIONS per row   |                  |
+-------------+----------------------------------+------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Active nav «Клиенты к разбору»
- [ ] Filters above table
- [ ] Row actions link to PAGE-004 / PAGE-007
- [ ] Optional Z-INSIGHT panel present
