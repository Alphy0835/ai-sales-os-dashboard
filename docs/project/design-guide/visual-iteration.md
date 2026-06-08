Doc ID: DESIGN-VISUAL-ITERATION-001
Status: draft
Source of truth: yes
Owner: design
Related docs: design-system-format/ui-kit.md, design-system-preview/design-system-preview.md, references/README.md, pages-map.md
Update together with: ui-kit.md, design-system-preview.md, references/*
Update trigger: новые референсы, обновление design guide или переработка preview
Review required: design, product
Maturity: L1

# Visual Iteration

План визуальной эволюции AI Sales OS. Структура и layout утверждаются отдельно от финального visual polish.

## Current State (v1 — branch `design/visual-foundation`)

| Item | Status | Notes |
|---|---|---|
| Layout shell | accepted | sidebar + main + insight |
| Zone map (PAGE-002) | accepted | KPI, trend, AI insight |
| Design tokens | draft | colors, typography, components |
| PAGE-002 HTML preview | review | **baseline** — функционально ок, визуально «типичный AI SaaS» |
| Moodboard refs | v1 | 3 PNG в `references/` |

**Решение:** v1 фиксируем в git как основу структуры. Визуальный слой перерабатываем в v2 после новых референсов и design guide от product.

## v2 — Planned (waiting for inputs)

Ожидаем от product:

- [ ] Дополнительные visual references (PNG/Figma links)
- [ ] Уточнённый design guide (отличия от v1, anti-patterns)
- [ ] Приоритет: что менять первым (sidebar, cards, typography, glow, charts)

Положить референсы в: `references/v2/`

## What Changes in v2 (expected)

| Area | v1 | v2 direction |
|---|---|---|
| Overall mood | generic dark glass AI dashboard | ближе к утверждённым референсам product |
| Glow / accents | blue/violet/cyan по шаблону | точечная калибровка, меньше «AI slop» |
| Typography | Inter default | возможна смена scale/weight по guide |
| Cards / metrics | uniform glass cards | иерархия, плотность, акценты по референсу |
| Charts | CSS placeholder | стиль линий/заливки по guide |
| Sidebar | standard pill active | по референсу (icon style, density) |
| AI insight panel | cyan left border + violet glow | softer или иной паттерн из guide |

**Не меняем без отдельного решения:** Page ID, zones, nav map, flow bindings.

## Workflow v2

1. Product кладёт refs → `references/v2/` + правки в design guide.
2. Обновить `colors.md`, `ui-kit.md`, `components-guidelines.md`.
3. Пересобрать `PAGE-002-manager-dashboard.md` (ASCII) → `.html`.
4. Product approve → status `active`, merge `design/visual-foundation` → `master`.
5. Остальные PAGE-xxx по тому же паттерну.

## File Checklist (agent prep)

When new refs arrive, update in order:

1. `references/v2/README.md` — index new refs
2. `design-system-format/colors.md`
3. `design-system-format/typography.md`
4. `design-system-format/components-guidelines.md`
5. `design-system-format/ui-kit.md` — Visual References table
6. `design-system-preview/PAGE-002-manager-dashboard.md`
7. `design-system-preview/PAGE-002-manager-dashboard.html`

## Related Docs

- `design-system-preview/PAGE-002-manager-dashboard.md`
- `references/README.md`
- `work-rules-design-guide.md`
