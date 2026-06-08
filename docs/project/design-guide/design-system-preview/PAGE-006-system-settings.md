Doc ID: DESIGN-PREVIEW-PAGE-006
Page ID: PAGE-006
Shell: SHELL-MANAGER
Status: draft preview
Related docs: ../pages-map.md, PAGE-006-system-settings.html

# System Settings — PAGE-006

Настройки критериев, отчётов, базы знаний и прав доступа.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | навигация | nav pills |
| Z-PAGE-HEADER | заголовок | title |
| Z-SET-CRITERIA | критерии оценки | criteria form (active tab) |
| Z-SET-REPORTS | кастомные отчёты | report templates |
| Z-SET-KB | база знаний | knowledge files |
| Z-SET-ACCESS | права сотрудников | access matrix |

## ASCII Wireframe

```
+-------------+----------------------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: Настройки         |
| *Settings   | [Criteria][Reports][KB][Access]  |
|             | Z-SET-CRITERIA (active):           |
|             |  criteria list + edit fields     |
+-------------+----------------------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Active nav «Настройки»
- [ ] Tab sub-nav for four sub-zones
- [ ] Criteria content visible by default
- [ ] Save action in toolbar
