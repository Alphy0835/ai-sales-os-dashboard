Doc ID: DESIGN-PREVIEW-PAGE-007
Page ID: PAGE-007
Shell: SHELL-MANAGER
Status: draft preview
Related docs: ../pages-map.md, PAGE-007-ai-agent-manager.html

# AI Agent (Manager) — PAGE-007

Диалог с AI-агентом в контексте клиента и записей.

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-SIDEBAR | навигация | nav pills |
| Z-PAGE-HEADER | заголовок | title |
| Z-CONTEXT | контекст клиента | client picker, comment, attach |
| Z-CHAT | диалог | messages, input, send |
| Z-SOURCES | RAG materials | collapsible refs |

## ASCII Wireframe

```
+-------------+----------------------------------+
| Z-SIDEBAR   | Z-PAGE-HEADER: AI-агент          |
| *AI Agent   | +----------+---------------------+ |
| (no insight)| | Z-CONTEXT| Z-CHAT              | |
|             | | client   | messages + input    | |
|             | | attach   | Z-SOURCES (hint)    | |
+-------------+----------------------------------+
```

## States

loading / empty / partial / error / forbidden

## Approval Checklist

- [ ] Active nav «AI-агент»
- [ ] `no-insight` class on app shell
- [ ] Context panel + chat layout
- [ ] Collapsible Z-SOURCES hint
