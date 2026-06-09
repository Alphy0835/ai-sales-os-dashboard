Doc ID: DESIGN-PREVIEW-PAGE-001
Page ID: PAGE-001
Shell: SHELL-AUTH
Status: implemented (apps/web)
Related docs: ../pages-map.md, PAGE-001-login.html, ../../frontend/frontend-docs.md, ../../architecture/api-contracts.md

# Login — PAGE-001

Центрированная форма входа. Shell без sidebar.

> Реализация: `apps/web/src/app/login/page.tsx` · API: `POST /api/v1/auth/login/`

## Zones

| Zone ID | Content | Components |
|---|---|---|
| Z-CENTER | карточка входа | glass card, logo |
| Z-FORM | поля формы | email, password, submit |
| Z-FOOTER | служебные ссылки | optional links |

## ASCII Wireframe

```
+--------------------------- SHELL-AUTH ---------------------------+
|                                                                  |
|                    +--------------------------------+            |
|                    | Z-CENTER                       |            |
|                    |  [Logo] AI Sales OS            |            |
|                    |  Z-FORM:                       |            |
|                    |    Email                       |            |
|                    |    Password                    |            |
|                    |    [ Войти ]                   |            |
|                    +--------------------------------+            |
|                    Z-FOOTER: забыли пароль?                      |
|                                                                  |
+------------------------------------------------------------------+
```

## States

loading / error / forbidden

## Approval Checklist

- [ ] Centered glass card on textured ambient
- [ ] Logo + form fields use recessed wells
- [ ] Primary submit uses cyan accent
- [ ] No sidebar or insight panel
