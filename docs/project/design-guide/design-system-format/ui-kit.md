Doc ID: DESIGN-UI-KIT-001
Status: draft
Source of truth: yes
Owner: design
Related docs: colors.md, typography.md, page-layout-rules.md, components-guidelines.md, ../pages-map.md
Update together with: colors.md, page-layout-rules.md, components-guidelines.md, ../pages-map.md
Update trigger: изменение визуального направления, glassmorphism или общих UI-правил
Review required: design, product
Maturity: L1

# UI Kit — AI Control Dashboard

Общий визуальный концепт AI Sales OS: premium AI SaaS dashboard в стиле dark glassmorphism.

> Палитра: `colors.md`  
> Layout: `page-layout-rules.md`  
> Компоненты: `components-guidelines.md`

## General Style

Интерфейс — **premium AI SaaS dashboard** для серьёзного B2B-инструмента контроля отдела продаж.

**Ощущение:** modern, expensive, calm, reliable, AI/productivity focused.

**Главная метафора:**

> Premium command center для AI-аналитики, базы знаний, контроля команды и рабочих процессов ОП.

### Visual References

Локальные референсы (структура и mood, не копировать 1:1):

| File | Что берём |
|---|---|
| `../references/ref-01-task-dashboard.png` | sidebar + glass cards + мягкий glow на active |
| `../references/ref-02-finance-dashboard.png` | layered panels, charts, right insight column |
| `../references/ref-03-analytics-dashboard.png` | dark navy base, cyan accent, metric cards grid |

### Do

- dark navy / black base
- frosted glass panels
- soft blue, violet, cyan glow accents
- large rounded cards
- calm futuristic UI
- high readability
- professional business tone

### Avoid

- cheap neon overload
- bright cyberpunk palette
- too many gradients
- childish illustrations
- heavy 3D effects
- aggressive crypto-trading aesthetic
- cluttered UI
- glow on every card («Christmas tree»)

## Main Visual Direction

- dark base background with subtle radial gradients
- layered glass panels (depth through transparency, not harsh shadows)
- soft glowing borders **only** on active / selected / primary elements
- large rounded corners (see `page-layout-rules.md`)
- clean spacing and clear hierarchy

## Glassmorphism (Summary)

Полные токены — в `colors.md` и `components-guidelines.md` → Glass Panel.

| Property | Value |
|---|---|
| Panel fill | `rgba(18, 25, 43, 0.72)` |
| Deep card | `rgba(10, 15, 28, 0.86)` |
| Border | `1px solid rgba(255,255,255,0.08)` |
| Backdrop blur | 16–24px |
| Glow | soft blue/violet — **только** active / primary / focus |

Не все карточки светятся одинаково.

## App Shell (Summary)

Трёхколоночный dashboard layout — детали в `page-layout-rules.md`:

```text
[ Z-SIDEBAR ] [ Z-MAIN — content ] [ Z-INSIGHT — optional ]
```

- **Z-SIDEBAR:** logo, nav, workspace (подразделение), settings, logout
- **Z-MAIN:** title, subtitle, actions, filters, cards grid, primary work area
- **Z-INSIGHT:** AI-сводка, быстрые метрики, заметки (скрывается на части экранов)

Навигация привязана к Page ID — см. `../pages-map.md`.

## Core Elements

| Element | Role |
|---|---|
| Sidebar nav item | primary navigation; active = blue/violet glow pill |
| Glass card | metrics, lists, forms, chat blocks |
| Primary button | main CTA; soft electric blue glow |
| Secondary button | ghost / outline on glass |
| Filter chip | period, status, priority filters |
| Metric value | large number + delta + sparkline |
| Status badge | success / warning / danger — muted, not neon |
| AI insight block | short summary with subtle accent border |

## Spacing Scale

| Token | px | Use |
|---|---|---|
| space-xs | 4 | inline gaps |
| space-sm | 8 | chip padding |
| space-md | 16 | card inner padding |
| space-lg | 24 | section gap |
| space-xl | 32 | page section margin |
| space-2xl | 48 | hero / title area |

## Radius Scale

| Token | px | Use |
|---|---|---|
| radius-sm | 8 | chips, inputs |
| radius-md | 12 | buttons |
| radius-lg | 16 | cards |
| radius-xl | 24 | panels, sidebar outer |
| radius-2xl | 32 | main shell container |

## Related Docs

- `colors.md`
- `typography.md`
- `page-layout-rules.md`
- `components-guidelines.md`
- `../pages-map.md`
