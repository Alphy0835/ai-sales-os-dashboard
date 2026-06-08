Doc ID: DESIGN-PREVIEW-PAGE-002
Page ID: PAGE-002
Shell: SHELL-MANAGER
Status: active (v2.5.1)
Source of truth: yes
Owner: design
Related docs: ../design-system-format/ui-design-direction.md, ../pages-map.md, PAGE-002-manager-dashboard.html
Update together with: PAGE-002-manager-dashboard.html
Maturity: L2

# Manager Dashboard — PAGE-002 (v2.5.1)

Texture `bacground.png` on app bg + cards/sidebar/wells. Shadows and blue glow preserved.

## Texture layers

| Surface | Overlay | Texture position |
|---|---|---|
| App (`.ambient`) | dark vignette + blue radials | `center`, fixed |
| Cards | `--texture-overlay-card` (alpha **0.72–0.84**) + tint **0.42** | `38% 24%` |
| Highlight cards | `--texture-overlay-card-hi` (**0.74–0.85**) + tint **0.44** | `45% 18%` |
| Sidebar | `--texture-overlay-shell` (**0.64–0.82**) + tint **0.47** | `62% 48%` |
| Wells (chart, mini KPI) | `--texture-overlay-well` | `72% 68%` |

## Zones

| Zone | Content |
|---|---|
| Z-SIDEBAR | logo, nav, workspace, settings, logout |
| Z-TOPBAR | breadcrumb, search, notify, profile, primary CTA |
| Z-KPI-HERO | circular KPI + main metric |
| Z-KPI-SECONDARY | compact metric cards |
| Z-ALERT-ACTION | alert / quick action |
| Z-TREND-CHART | analytics chart (cyan contour line) |
| Z-AI-RECOMMENDATION | AI insight + confidence + sources |
| Z-EMPLOYEE-TABLE | performance table |
| Z-SOURCES-STATUS | CRM / telephony status |
| Z-INSIGHT | right panel widgets |

## ASCII Wireframe

```
+--------------------------------------------------------------------------------+
| SIDEBAR | TOPBAR: Home / Dashboard    [search........]  [@] [Run AI Analysis] |
|         +------------------------------+---------------------------+-----------+|
| Logo    | [KPI ring] [KPI cards x2]    [Alert card]               | Insight   ||
| *Dash   +------------------------------+---------------------------+ widgets ||
| Clients | [======== Chart ========]  | [AI Recommendation]       |           ||
| ...     +------------------------------+---------------------------+           ||
|         | [Employee table ==========]  | [Sources status]          |           ||
+---------+------------------------------------------------------------------------+
```

## Approval Checklist

- [ ] Premium 3D depth — not flat/terminal
- [ ] Hero KPI dominant (large ring + number + glow)
- [ ] Soft blue ambient behind dashboard area
- [ ] Dark base + cyan accents — no orange
- [ ] Top bar + 3-row grid (layout unchanged)
- [ ] AI block shows confidence + sources
- [ ] Green only on success deltas/status
