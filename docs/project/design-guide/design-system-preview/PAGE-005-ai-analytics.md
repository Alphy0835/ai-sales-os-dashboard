Doc ID: DESIGN-PREVIEW-PAGE-005
Page ID: PAGE-005
Shell: SHELL-MANAGER
Status: draft preview
Related docs: ../pages-map.md, PAGE-005-ai-analytics.html

# AI Analytics — PAGE-005

Запуск AI-отчётов и просмотр результатов анализа.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | навигация | nav pills |
| Z-PAGE-HEADER | заголовок | title |
| Z-SCOPE | объект анализа | employee / subdivision select |
| Z-REPORT-PICKER | шаблон отчёта | template list |
| Z-RUN | запуск | primary button |
| Z-CANVAS | результат | chart + AI insight |
| Z-ACTIONS | действия | link to PAGE-004 |

## ASCII Wireframe

```
+-------------+----------------------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: AI-аналитика      |
| *Analytics  | Z-SCOPE | Z-REPORT-PICKER        |
|             | [ Z-RUN: Запустить анализ ]      |
|             | Z-CANVAS: [chart] [AI insight]   |
|             | Z-ACTIONS: вынести на разбор     |
+-------------+----------------------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Active nav «AI-аналитика»
- [ ] Scope + report picker + run button
- [ ] Canvas with chart and AI block
- [ ] Action links to review history
