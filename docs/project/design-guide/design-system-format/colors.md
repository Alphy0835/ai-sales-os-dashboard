Doc ID: DESIGN-COLORS-001
Status: draft
Source of truth: yes
Owner: design
Related docs: ui-kit.md, components-guidelines.md, typography.md
Update together with: ui-kit.md, components-guidelines.md
Update trigger: изменение токена цвета или правил accent/status
Review required: design
Maturity: L1

# Colors

Палитра AI Control Dashboard. CSS-переменные — рекомендуемые имена для preview HTML и frontend.

## Base Colors

| Token | Value | Use |
|---|---|---|
| `--bg-main` | `#070B14` | main app background |
| `--bg-secondary` | `#0D1323` | secondary layer, sidebar backdrop |
| `--bg-panel` | `rgba(18, 25, 43, 0.72)` | glass panels |
| `--bg-card-deep` | `rgba(10, 15, 28, 0.86)` | nested cards, tables |
| `--bg-elevated` | `rgba(24, 32, 54, 0.78)` | hover / elevated glass |

### Background Gradients

Subtle radial only — не доминируют над контентом:

| Token | Example | Use |
|---|---|---|
| `--gradient-ambient` | `radial-gradient(ellipse at 20% 0%, rgba(59,108,255,0.12), transparent 50%)` | top-left ambient |
| `--gradient-ambient-2` | `radial-gradient(ellipse at 80% 100%, rgba(124,92,255,0.08), transparent 45%)` | bottom-right depth |

## Text Colors

| Token | Value | Use |
|---|---|---|
| `--text-primary` | `#F4F7FF` | titles, key metrics |
| `--text-secondary` | `#A8B3CF` | labels, descriptions |
| `--text-muted` | `#6B7898` | placeholders, inactive nav |
| `--text-inverse` | `#070B14` | text on bright accent (rare) |

Конtrast: primary text on `--bg-panel` — high readability обязательна.

## Accent Colors

Primary accents — использовать точечно:

| Token | Value | Use |
|---|---|---|
| `--accent-blue` | `#3B6CFF` | primary CTA, active nav, links |
| `--accent-violet` | `#7C5CFF` | secondary highlight, charts |
| `--accent-cyan` | `#28E0D4` | AI blocks, live indicators |

Premium secondary:

| Token | Value | Use |
|---|---|---|
| `--accent-gold` | `#D6B56D` | premium badges, achievements (sparingly) |

### Glow (Active Only)

| Token | Value | Use |
|---|---|---|
| `--glow-blue` | `0 0 24px rgba(59, 108, 255, 0.35)` | active nav, primary button |
| `--glow-violet` | `0 0 20px rgba(124, 92, 255, 0.25)` | focused card, AI panel |
| `--border-glass` | `rgba(255, 255, 255, 0.08)` | all glass borders |

## Status Colors

Muted, не кислотные:

| Token | Value | Use |
|---|---|---|
| `--status-success` | `#34D399` | positive delta, done |
| `--status-warning` | `#FBBF24` | attention, at risk |
| `--status-danger` | `#F87171` | critical, failure |
| `--status-info` | `#60A5FA` | neutral info |

Status backgrounds for badges: 10–15% opacity fill + border same hue at 25% opacity.

## Rules

1. Один экран — 1–2 accent цвета доминируют; остальное нейтральное стекло.
2. Glow только у active / primary / AI-focus — не у каждой карточки.
3. Success/warning/danger — для данных и статусов, не для декора.
4. Gold — редко (похвала, premium insight).

## Related Docs

- `ui-kit.md`
- `components-guidelines.md`
