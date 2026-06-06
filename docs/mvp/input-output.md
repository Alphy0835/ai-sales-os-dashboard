# MVP: Input / Output

← [mvp-scope.md](../project/features/mvp-scope.md) · [data-flow-mvp.md](../architecture/data-flow-mvp.md)

---

## Input

| Input | Обязательность | Формат |
|-------|----------------|--------|
| Аудиофайл звонка | один из двух* | MP3, WAV, M4A |
| Транскрипт | один из двух* | TXT, MD, paste |
| Pipeline | ✅ | UI |
| Quality Criteria | ✅ | UI |
| База знаний | ✅ | TXT, MD (+ PDF) |
| Сотрудники | ✅ | UI / CSV |
| CSV сделок | опционально | deal_id, employee, stage, date |

\* Audio **или** transcript — не оба.

### Минимум для первого анализа

```
Workspace → Pipeline (≥1 stage) → Criteria (≥1) → Knowledge (≥1 doc) → Employee → Call
```

---

## Output

### Touchpoint (Evaluation)

| Field | Описание |
|-------|----------|
| **score** | 0–100 или 1–5 + breakdown по criteria |
| **summary** | 3–5 предложений |
| **strengths** | С привязкой к criteria / цитатами |
| **weaknesses** | Нарушения criteria |
| **recommendations** | Конкретные действия |

### Employee Profile

- История evaluations
- Growth zones (≥2 evaluations с повторяющимися weaknesses)
- Средний score

### Manager Card

- Manager summary по команде
- Список сотрудников + last score
- Drill-down → Employee Profile
