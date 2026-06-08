Doc ID: DESIGN-PREVIEW-RULES-001
Status: draft
Source of truth: yes
Owner: design
Related docs: docs/project/design-guide/pages-map.md, docs/project/design-guide/work-rules-design-guide.md, docs/project/design-guide/design-system-preview/design-system-preview.md
Update together with: pages-map.md, design-system-preview.md, work-rules-design-guide.md
Update trigger: изменение формата preview-файлов или pipeline ASCII → HTML
Review required: design
Maturity: L1

# Work Rules — Design System Preview

Папка `design-system-preview/` — ASCII-wireframes и HTML-рендер страниц до frontend-реализации.

## Файлы папки

| Файл | Назначение |
|---|---|
| `work-rules-design-system-preview.md` | правила папки (этот файл) |
| `design-system-preview.md` | индекс всех preview-страниц |
| `PAGE-xxx-slug.md` | спека страницы + ASCII-макет (source of truth) |
| `PAGE-xxx-slug.html` | HTML-визуализация по `.md` |

## Структура `PAGE-xxx-slug.md`

```markdown
Doc ID: DESIGN-PREVIEW-PAGE-xxx
Page ID: PAGE-xxx
Shell: SHELL-MANAGER | SHELL-EMPLOYEE | SHELL-AUTH
Related docs: pages-map.md, user-flow FLOW-xxx

# {Page Name}

## Zones
| Zone ID | Content | Components |

## ASCII Wireframe
(блок +---+)

## States
loading / empty / partial / error / forbidden

## Links
→ PAGE-xxx
```

## ASCII

- Зоны подписывать ID из `pages-map.md` (`Z-MAIN`, `Z-NAV`, …).
- Shell рисовать полностью; уникальный контент — внутри Z-MAIN.
- Box-drawing: `+ - |`.

## HTML

- Секции с `id` или `data-zone` = Zone ID.
- Не добавлять UI-блоки вне `.md`-спеки.
- Стили: `design-system-format/colors.md`, `typography.md`, `page-layout-rules.md` (когда заполнены).

## Sync

| Если меняется | Обновить |
|---|---|
| `pages-map.md` (зоны, nav) | preview `.md` → `.html` |
| preview `.md` | `.html` |
| `design-system-format/*` | все `.html` при смене токенов |

## Related Docs

- `../pages-map.md`
- `../work-rules-design-guide.md`
- `design-system-preview.md`
