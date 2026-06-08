Doc ID: DESIGN-COLORS-001
Status: active
Source of truth: yes
Owner: design
Related docs: ui-design-direction.md, ui-kit.md, components-guidelines.md
Update together with: ui-kit.md, components-guidelines.md
Update trigger: изменение palette или accent rules
Review required: design
Maturity: L2

# Colors

Calm dark slate-blue palette. **Contour accents** (border/outline), not saturated fills. Green — success only.

> Direction: `ui-design-direction.md`

## Base Colors

| Token | Value | Use |
|---|---|---|
| `--bg-app` | `#0A0D12` | app background |
| `--bg-surface` | `#0E1219` | main surface |
| `--bg-sidebar` | `#0A0D11` | sidebar |
| `--bg-card` | `#111820` | card base |
| `--bg-card-elevated` | `#161E28` | elevated card |
| `--bg-panel-soft` | `rgba(16, 22, 32, 0.86)` | soft panels |

## Text

| Token | Value | Use |
|---|---|---|
| `--text-primary` | `#E8ECF1` | titles, KPI numbers |
| `--text-secondary` | `#9AA3AE` | body, labels |
| `--text-muted` | `#5C6773` | meta, placeholders |
| `--text-disabled` | `#404850` | disabled |

## Accents (contour-first)

| Token | Value | Use |
|---|---|---|
| `--accent-blue` | `#4A7BA7` | muted deep blue |
| `--accent-blue-deep` | `#2A4A6B` | shadows, ambient |
| `--accent-cyan` | `#6BA3C7` | primary contour, charts, active text |
| `--accent-cyan-soft` | `#5B8FA8` | secondary labels |
| `--accent-contour` | `rgba(107, 163, 199, 0.42)` | default accent border |
| `--accent-contour-strong` | `rgba(107, 163, 199, 0.62)` | CTA / active contour |

## Status (functional only)

| Token | Value | Use |
|---|---|---|
| `--status-success` | `#22C55E` | growth, done, healthy |
| `--status-warning` | `#C9A227` | attention (muted) |
| `--status-error` | `#CF5C5C` | critical (muted) |

## Gradients

| Token | Value | Use |
|---|---|---|
| `--gradient-chart-fill` | `linear-gradient(180deg, rgba(107,163,199,0.14), rgba(107,163,199,0.01))` | chart area |
| `--gradient-card-cool` | `radial-gradient(circle at top right, rgba(74,123,167,0.06), transparent 35%)` | highlighted cards |

No orange/violet gradient fills. Primary CTA — contour button, not gradient fill.

## Borders, Shadows & 3D Volume

Reference: `../references/ref-04-card-volume-3d.png`

| Token | Value | Use |
|---|---|---|
| `--border-subtle` | `rgba(255, 255, 255, 0.05)` | default borders |
| `--border-active` | `rgba(107, 163, 199, 0.38)` | active/highlight |
| `--surface-card` | blue-tinted dark gradient | raised card face |
| `--surface-card-highlight` | slightly lighter blue tint | hero / AI cards |
| `--shadow-raised` | multi-layer soft outer | card elevation |
| `--shadow-raised-bevel` | inset top-left highlight | bevel |
| `--shadow-recessed` | inset dark wells | inputs, gauges |
| `--shadow-active` | raised + soft blue ambient | highlighted cards |
| `--glow-cool-soft` | `0 0 24px rgba(74, 123, 167, 0.1)` | hover accents |

## Rules

1. Accents — **contour** (1px border, transparent/minimal fill), not solid fills.
2. No neon cyan / electric blue; keep accents muted and calm.
3. Chart lines: `--accent-cyan`; fill very subtle.
4. Active sidebar / chips / badges: border accent, not filled pill.
5. Green / amber / red — status only, also prefer contour badges.
