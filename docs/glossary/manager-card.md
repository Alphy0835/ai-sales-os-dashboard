# Manager Card (MVP)

← [ui-mvp.md](./ui-mvp.md) · [product-glossary.md](../../product-glossary.md)

Экран руководителя в MVP — простой дашборд команды, без алертов и прогнозов.

---

## Что показывает

| Блок | Содержание |
|------|------------|
| **Список сотрудников** | Все employees workspace с базовой информацией |
| **Последняя оценка** | Last score + дата последней evaluation у каждого |
| **Средний score** | По сотруднику (если ≥1 evaluation) и агрегат по команде |
| **Обработанные звонки** | Количество touchpoints / evaluations на сотрудника |
| **Growth zones** | Топ повторяющихся зон роста по команде |
| **Drill-down** | Клик на сотрудника → Employee Profile |
| **Evaluation Detail** | Клик на evaluation → полный разбор touchpoint |

---

## Что не показывает (post-MVP)

- Сигналы просадки до P&L
- Прогнозы выручки
- Иерархия (тимлид → РГП → ДП)
- Очередь действий / алерты
- Фильтры по stage, периоду, deal

---

## Минимальная структура экрана

```
┌─────────────────────────────────────────────────┐
│  Manager Card                          [period] │
├─────────────────────────────────────────────────┤
│  Team summary: avg score · total evaluations    │
│  Top growth zones: [zone 1] [zone 2] [zone 3]   │
├─────────────────────────────────────────────────┤
│  Employee          Last score  Calls  Avg  →    │
│  ─────────────────────────────────────────────  │
│  Алексей Петров    72         3      68   [→]   │
│  ...                                            │
└─────────────────────────────────────────────────┘
         │ click employee              │ click score
         ▼                             ▼
   Employee Profile              Evaluation Detail
```

---

## Связанные термины

- [Employee Profile](./entities.md) — карточка сотрудника
- [Evaluation Detail](./ui-mvp.md) — разбор одного touchpoint
- [Growth Zone](./evaluation.md) — зона роста
