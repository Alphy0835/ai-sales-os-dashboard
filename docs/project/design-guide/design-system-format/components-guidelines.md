Doc ID: DESIGN-COMPONENTS-001
Status: active
Source of truth: yes
Owner: design
Related docs: colors.md, ui-design-direction.md
Update together with: colors.md
Update trigger: новый component pattern
Review required: design
Maturity: L2

# Components Guidelines

## Card (base) — 3D volume

Reference: `references/ref-04-card-volume-3d.png` — **volume/depth only**, not color.

**Raised card** (`.card`):

```css
background: var(--surface-card);
border: 1px solid rgba(255,255,255,0.05);
border-bottom-color: rgba(0,0,0,0.35);
border-right-color: rgba(0,0,0,0.25);
border-radius: 28px;
box-shadow: var(--shadow-raised), var(--shadow-raised-bevel);
```

Optional `::before` — cool radial overlay at top-right (`--gradient-card-cool`).

**Highlighted card** (`.card-highlight`): `--surface-card-highlight`, `--shadow-active`, `--accent-contour` border.

**Recessed well** (`.recessed`): inputs, chart areas, mini-metrics, tags inside cards.

```css
background: linear-gradient(180deg, rgba(6,7,8,0.95), rgba(14,16,18,0.75));
border: 1px solid rgba(0,0,0,0.4);
border-bottom-color: rgba(255,255,255,0.03);
box-shadow: var(--shadow-recessed);
```

**Rules:** light source top-left; soft wide outer shadows; inset shadows for carved elements; no sharp high-contrast shadows.

## MetricCard / Circular KPI

- label (meta), large number, delta (green/red only for data)
- optional circular progress ring — **contour arc** cyan stroke + recessed inner disc
- optional sparkline (cyan, muted)

## ChartCard

- cyan line (`--accent-cyan`) + subtle `--gradient-chart-fill`
- muted grid, no rainbow
- short AI insight line below chart

## AIInsightCard

- label «AI Recommendation» — **contour badge**
- confidence badge, source tags (contour pills)
- suggested action (secondary contour button)
- highlighted card: `--accent-contour` border, no violet fill

## TableCard

- compact dark rows, hover `rgba(255,255,255,0.03)`
- status badges: success/warning/error tokens only

## Primary Button

- **contour CTA**: transparent/dark fill, `--accent-contour-strong` border, `--accent-cyan` text
- radius 16px, soft hover glow
- **one per screen**

## Secondary Button

- contour outline: `--accent-contour` border, transparent bg, cyan-muted text

## Input / Search

- **recessed well** styling (`--shadow-recessed`), not flat transparent
- focus: cyan contour border + subtle outer ring

## Sidebar Nav Item

- inactive: `--text-muted`
- active: contour border `--accent-contour`, subtle `rgba(107,163,199,0.05)` bg, cyan text

## Badge

- pill, 11–13px, **contour** style: transparent bg + 1px border in status color

## AI Explainability Block

Every AI output shows: analyzed scope · confidence · sources · suggested action · optional warning
