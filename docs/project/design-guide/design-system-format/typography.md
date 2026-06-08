Doc ID: DESIGN-TYPO-001
Status: draft
Source of truth: yes
Owner: design
Related docs: ui-kit.md, colors.md
Update together with: ui-kit.md, colors.md
Update trigger: изменение шрифта, scale или правил иерархии
Review required: design
Maturity: L1

# Typography

Типографика для dark glass UI: читаемость на полупрозрачных панелях.

## Font Family

| Token | Stack | Use |
|---|---|---|
| `--font-sans` | `'Inter', 'Segoe UI', system-ui, sans-serif` | весь UI |
| `--font-mono` | `'JetBrains Mono', 'Consolas', monospace` | IDs, код, метрики API (опционально) |

Inter — primary. Fallback system sans для preview HTML без webfont.

## Headings

| Style | Size / Line / Weight | Use |
|---|---|---|
| H1 | 32px / 40px / 700 | page title (Z-PAGE-HEADER) |
| H2 | 24px / 32px / 600 | section title inside Z-MAIN |
| H3 | 20px / 28px / 600 | card title |
| H4 | 16px / 24px / 600 | sub-section, table group |

Color: `--text-primary`. Letter-spacing H1: `-0.02em`.

## Body Text

| Style | Size / Line / Weight | Use |
|---|---|---|
| Body | 16px / 24px / 400 | main content |
| Body sm | 14px / 20px / 400 | table cells, descriptions |
| Caption | 12px / 16px / 400 | meta, timestamps |
| Label | 12px / 16px / 500 | form labels, uppercase nav (optional) |

Color: body → `--text-secondary`; caption → `--text-muted`.

## Metric Display

| Style | Size / Line / Weight | Use |
|---|---|---|
| Metric xl | 36px / 44px / 700 | KPI hero numbers |
| Metric lg | 28px / 36px / 700 | card KPI |
| Metric delta | 14px / 20px / 500 | +/- change with status color |

## Rules

- Max 2 heading levels на одном экране без вложенной структуры.
- Не использовать light font weight (<400) on dark glass — плохая читаемость.
- AI-generated text blocks — Body sm, `--text-secondary`.
- Truncate long labels with ellipsis; full text in tooltip.

## Related Docs

- `ui-kit.md`
- `colors.md`
