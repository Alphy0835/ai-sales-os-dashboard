# AI Sales OS Dashboard

> Навигация: [README.md](./README.md) · [product-glossary.md](./product-glossary.md)

## The Idea

Операционная система для отделов продаж. Закрывает разрыв между CRM (что произошло) и качеством работы (как и почему).

Анализирует коммуникации → связывает с базой знаний и pipeline → выдаёт **действия**: просадки, зоны роста, рекомендации.

| Роль | Ценность |
|------|----------|
| **Руководитель** | Картина контура, сигналы до P&L, план развития |
| **Менеджер** | Динамика, зоны роста, рекомендации *(post-MVP: Employee View)* |

---

## The Flow

Как пользователь работает с продуктом.

| Этап | Summary | Детали |
|------|---------|--------|
| **Онбординг** | Вход → pipeline → база знаний → данные → первый анализ | [docs/flow/onboarding.md](./docs/flow/onboarding.md) |
| **Ежедневный цикл** | Данные → AI → открыл → получил → действуешь | [docs/flow/daily-cycle.md](./docs/flow/daily-cycle.md) |
| **Post-MVP сценарии** | Подготовка к касанию, просадка, сложная сделка | [docs/flow/scenarios-post-mvp.md](./docs/flow/scenarios-post-mvp.md) |

---

## Why It Matters

CRM показывает «что», ОКК не масштабируется, просадки видны поздно. Система даёт сквозной контроль качества **в процессе**.

→ [docs/product/why-it-matters.md](./docs/product/why-it-matters.md)

---

## How It Works

**MVP:** upload (audio \| transcript) → AI analysis → evaluation → employee profile + manager card

→ [docs/architecture/data-flow-mvp.md](./docs/architecture/data-flow-mvp.md)

| Блок | Summary | Детали |
|------|---------|--------|
| **Модули** | Pipeline Builder, Communication Intelligence, Knowledge Engine, People Development + post-MVP | [docs/architecture/modules.md](./docs/architecture/modules.md) |
| **Роли** | Admin, Manager, Employee (+ post-MVP: иерархия) | [docs/architecture/roles.md](./docs/architecture/roles.md) |

---

## MVP vs Roadmap

**MVP =** звонок + pipeline + criteria + knowledge base → score + growth zones + manager card.

→ [docs/progect/feauters/mvp-scope.md](./docs/progect/feauters/mvp-scope.md) · [docs/product/roadmap.md](./docs/product/roadmap.md) · [demo-scenario-1.md](./docs/progect/feauters/demo-scenario-1.md)
