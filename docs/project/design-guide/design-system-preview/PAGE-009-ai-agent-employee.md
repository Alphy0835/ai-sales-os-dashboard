Doc ID: DESIGN-PREVIEW-PAGE-009
Page ID: PAGE-009
Shell: SHELL-EMPLOYEE
Status: draft preview
Related docs: ../pages-map.md, PAGE-009-ai-agent-employee.html

# AI Agent (Employee) — PAGE-009

AI-агент для сотрудника с ограниченным контекстом.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | nav (2 items) | Dashboard, AI Agent |
| Z-PAGE-HEADER | заголовок | title |
| Z-LIMIT-NOTICE | ограничение прав | optional banner |
| Z-CHAT | диалог | messages, input |
| Z-CONTEXT | минимальный контекст | client attach (if allowed) |

## ASCII Wireframe

```
+-------------+----------------------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: AI-агент          |
|   Dashboard | Z-LIMIT-NOTICE (optional banner) |
| *AI Agent   | Z-CHAT: messages + input         |
|   Logout    | Z-CONTEXT: minimal attach        |
+-------------+----------------------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Active nav «AI-агент»
- [ ] Optional limit notice banner
- [ ] Chat as primary content
- [ ] Minimal context panel
