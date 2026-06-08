Doc ID: DESIGN-DIRECTION-001
Status: active
Source of truth: yes
Owner: design
Related docs: ui-kit.md, colors.md, page-layout-rules.md, components-guidelines.md, typography.md, ../visual-iteration.md
Update together with: colors.md, ui-kit.md, components-guidelines.md
Update trigger: изменение visual direction от product
Review required: design, product
Maturity: L2

# UI Design Direction

Premium dark AI SaaS dashboard для business users. Комбинация трёх референсов:

1. **Layout** (ref-01) — sidebar, top bar, central analytics, compact metrics, tables, optional right panel.
2. **Colors** — deep slate/navy base, calm blue-cyan **contour** accents, green только для success.
3. **Cards** (ref-03 + ref-04) — large rounded dark cards, soft 3D depth, circular KPI, neumorphic feel.

**Mood:** serious, expensive, calm, analytical, trustworthy — не crypto-neon, не gaming.

> Токены: `colors.md` · Компоненты: `components-guidelines.md` · Layout: `page-layout-rules.md`

## Hard Rules

- No neon / electric blue dashboard
- No crypto/gaming aesthetic
- No gradient overload or orange/violet fill CTAs
- Accents — **contour-first** (border/outline), minimal fill
- Green — only success/status
- Primary CTA — one per screen (contour button, cyan border)
- Glow — only active/important elements, soft blue
- AI results — explainable (confidence, sources, suggested action)

## Layout

```text
[Left Sidebar] [Main: TopBar + Content Grid] [Optional Right Panel]
```

**Main content grid (dashboard):**

| Row | Blocks |
|---|---|
| Top | Main KPI / AI Summary · Secondary KPI · Action/Alert |
| Middle | Large Analytics Chart · AI Insight Panel |
| Bottom | Activity/Reports Table · Status/Sources |

Dense professional dashboard, not cluttered.

## AI UX Labels

Use: AI Recommendation, Confidence, Sources, Suggested Action, Analysis Status, Knowledge Match.

Avoid: Magic, Super AI, God Mode.

## Implementation Priority

Reusable components: AppShell, Sidebar, TopBar, Card, MetricCard, ChartCard, AIInsightCard, TableCard, Button, Input, Badge, StatusIndicator.

First screens: Login, Dashboard, AI Assistant, Knowledge Base, Analytics, Employees, Reports, Settings.

## Related Docs

- `../references/` — moodboard v1
- `../design-system-preview/PAGE-002-manager-dashboard.html` — reference implementation
