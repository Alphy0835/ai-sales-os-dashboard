Doc ID: DESIGN-COMPONENTS-001
Status: draft
Source of truth: yes
Owner: design
Related docs: ui-kit.md, colors.md, typography.md, page-layout-rules.md
Update together with: ui-kit.md, colors.md
Update trigger: новый компонент или изменение states/interaction
Review required: design
Maturity: L1

# Components Guidelines

Компоненты AI Control Dashboard. Preview и frontend следуют этим правилам.

## Glass Panel

Base container for sidebar, cards, modals.

| Property | Value |
|---|---|
| background | `--bg-panel` |
| border | 1px solid `--border-glass` |
| backdrop-filter | blur(20px) |
| border-radius | `--radius-lg` to `--radius-xl` |
| shadow | none default; `--glow-*` only when `.is-active` or `.is-primary` |

Variants:

| Variant | Background | Glow |
|---|---|---|
| default | `--bg-panel` | no |
| deep | `--bg-card-deep` | no |
| active | `--bg-panel` | `--glow-blue` |
| ai-focus | `--bg-panel` | `--glow-violet` + left border 2px `--accent-cyan` |

## Sidebar Navigation

| State | Style |
|---|---|
| default | `--text-muted`, transparent bg |
| hover | `--text-secondary`, `rgba(255,255,255,0.04)` bg |
| active | `--text-primary`, pill bg `rgba(59,108,255,0.15)`, `--glow-blue`, icon `--accent-blue` |

Item: icon 20px + label Body sm, height 44px, radius-md, gap 12px.

Footer block: Settings + Logout separated by 1px `--border-glass`.

## Buttons

### Primary

- bg: linear-gradient(135deg, `--accent-blue`, `#2B5AE0`)
- text: `--text-primary`
- radius: `--radius-md`
- padding: 12px 20px
- glow: `--glow-blue` on hover only
- use: one main action per toolbar

### Secondary (Ghost)

- bg: transparent
- border: 1px `--border-glass`
- text: `--text-secondary`
- hover: `rgba(255,255,255,0.06)` bg

### Danger

- bg: `rgba(248, 113, 113, 0.15)`
- text: `--status-danger`
- no glow unless destructive confirm

## Inputs

- bg: `rgba(0,0,0,0.25)` inside glass card
- border: 1px `--border-glass`
- focus: border `--accent-blue`, subtle `--glow-blue`
- placeholder: `--text-muted`
- height: 44px (default), radius-sm

Search in header: full-width in top of Z-MAIN optional, icon left.

## Filter Chips

- height: 32px, radius-full or radius-sm
- default: ghost border
- selected: `rgba(59,108,255,0.2)` bg, `--accent-blue` text
- use: period (today/week/month), status filters

## Cards

### Metric Card

```
+---------------------------+
| label (caption)           |
| METRIC VALUE (metric lg)  |
| delta + sparkline         |
+---------------------------+
```

- deep glass variant
- delta green/red per `--status-*`
- optional mini chart bottom 40px height

### List Card (clients, reviews)

- row height 56–64px
- hover: `rgba(255,255,255,0.03)`
- row actions: ghost icon buttons right

### AI Insight Card

- ai-focus variant
- icon cyan + short bullet list
- max 5 lines before «подробнее»

## Tables

- header: Caption uppercase, `--text-muted`
- row border-bottom: `rgba(255,255,255,0.06)`
- zebra: optional `rgba(255,255,255,0.02)`
- sticky header inside scrollable deep glass container

## Chat (AI Agent)

| Zone | Component |
|---|---|
| message list | scrollable deep glass |
| user bubble | `--bg-elevated`, align right |
| ai bubble | ai-focus left border, align left |
| input bar | fixed bottom, input + send primary icon button |
| context attach | chips above input |

## Status Badges

- padding 4px 10px, radius-full, Caption weight 500
- success / warning / danger / info — fill 12% opacity + matching text

## Loading / Empty / Error

| State | Pattern |
|---|---|
| loading | skeleton bars on glass, shimmer subtle |
| empty | centered icon muted + Body sm + secondary CTA |
| partial | banner top of Z-CONTENT, `--status-warning` border |
| error | `--status-danger` icon + retry secondary button |
| forbidden | lock icon + «Нет доступа» Body |

## Related Docs

- `ui-kit.md`
- `colors.md`
- `page-layout-rules.md`
