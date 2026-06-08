# Architecture: Data Flow (MVP)

← [project-idea.md](../../project-idea.md) · [input-output.md](../mvp/input-output.md)

```
Upload (audio | transcript + employee + stage)
        │
        ▼
  Transcribe (if audio)
        │
        ▼
  AI Analysis ← pipeline criteria + knowledge base
        │
        ▼
  Evaluation (score, summary, strengths, weaknesses, recommendations)
        │
        ├──► Employee Profile (history, growth zones)
        └──► Manager Card (team summary, drill-down)
```

## Input (MVP)

| Input | Обязательно |
|-------|-------------|
| Audio или transcript | ✅ один из двух |
| Pipeline + criteria | ✅ |
| Knowledge base | ✅ |
| Employees | ✅ |
| CSV сделок | опционально |

## Output (MVP)

| Output | Уровень |
|--------|---------|
| score, summary, strengths, weaknesses, recommendations | Touchpoint |
| history, growth zones | Employee Profile |
| manager summary, drill-down | Manager Card |
