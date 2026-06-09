"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchMe } from "@/lib/api";
import {
  fetchKnowledgeGrants,
  fetchPermissionAudit,
  fetchPermissionUsers,
  fetchScopeUsers,
  LEVEL_OPTIONS,
  MODULE_LABELS,
  PERMISSION_MODULES,
  updateKnowledgeGrants,
  updateUserPermissions,
  type AuditLogEntry,
  type KnowledgeGrant,
  type PermissionUser,
} from "@/lib/permissions-api";
import { SettingsPanelShell } from "@/components/SettingsPanelShell";

export function AccessSettingsView() {
  const [users, setUsers] = useState<PermissionUser[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [permissions, setPermissions] = useState<Record<string, string>>({});
  const [grants, setGrants] = useState<KnowledgeGrant[]>([]);
  const [audit, setAudit] = useState<AuditLogEntry[]>([]);
  const [canEdit, setCanEdit] = useState(false);
  const [canView, setCanView] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const me = await fetchMe();
      const settingsPerm = me.permissions.settings ?? "none";
      setCanEdit(settingsPerm === "edit");
      setCanView(settingsPerm === "edit" || settingsPerm === "view");
      if (settingsPerm === "none") {
        setUsers([]);
        return;
      }
      const [permUsers, scope] = await Promise.all([fetchPermissionUsers(), fetchScopeUsers()]);
      const scopedIds = new Set(scope.users.map((u) => u.id));
      const list = permUsers.results.filter((u) => scopedIds.has(u.id) && u.id !== me.id);
      setUsers(list);
      if (!selectedId && list.length) {
        setSelectedId(list[0].id);
      }
      const auditRes = await fetchPermissionAudit();
      setAudit(auditRes.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!selectedId || !canView) return;
    (async () => {
      try {
        const user = users.find((u) => u.id === selectedId);
        if (user) {
          setPermissions({ ...user.permissions });
        }
        const kg = await fetchKnowledgeGrants(selectedId);
        setGrants(kg.grants);
        const auditRes = await fetchPermissionAudit(selectedId);
        setAudit(auditRes.results);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка загрузки прав");
      }
    })();
  }, [selectedId, canView, users]);

  const onSaveModules = async () => {
    if (!canEdit || !selectedId) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await updateUserPermissions(selectedId, permissions);
      setSuccess("Права модулей сохранены");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить права");
    } finally {
      setSaving(false);
    }
  };

  const onSaveGrants = async () => {
    if (!canEdit || !selectedId) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = grants
        .filter((g) => g.is_allowed !== null && g.grantor_can_assign)
        .map((g) => ({ article_id: g.article_id, is_allowed: g.is_allowed as boolean }));
      await updateKnowledgeGrants(selectedId, payload);
      setSuccess("Права на базу знаний сохранены");
      const kg = await fetchKnowledgeGrants(selectedId);
      setGrants(kg.grants);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить права KB");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="muted">Загрузка…</p>;
  }

  if (!canView) {
    return <p className="muted">Нет доступа к управлению правами.</p>;
  }

  return (
    <SettingsPanelShell>
      {error ? <p className="error-text">{error}</p> : null}
      {success ? <p className="success-text">{success}</p> : null}

      <div className="access-toolbar">
        <label className="field-label">
          Сотрудник
          <select
            className="select-input"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name} ({u.email})
              </option>
            ))}
          </select>
        </label>
      </div>

      <h3 className="settings-section-title">Модули</h3>
      <div className="access-matrix-wrap">
        <table className="access-matrix">
          <thead>
            <tr>
              <th>Модуль</th>
              {LEVEL_OPTIONS.map((level) => (
                <th key={level}>{level}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERMISSION_MODULES.map((mod) => (
              <tr key={mod}>
                <td>{MODULE_LABELS[mod] ?? mod}</td>
                {LEVEL_OPTIONS.map((level) => (
                  <td key={level}>
                    <input
                      type="radio"
                      name={`perm-${mod}`}
                      checked={(permissions[mod] ?? "none") === level}
                      disabled={!canEdit}
                      onChange={() => setPermissions((prev) => ({ ...prev, [mod]: level }))}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {canEdit ? (
        <button type="button" className="btn btn-primary" disabled={saving || !selectedId} onClick={onSaveModules}>
          Сохранить модули
        </button>
      ) : null}

      <h3 className="settings-section-title">База знаний (per-user)</h3>
      <div className="access-matrix-wrap">
        <table className="access-matrix access-matrix-kb">
          <thead>
            <tr>
              <th>Статья</th>
              <th>Уровень</th>
              <th>Базовый доступ</th>
              <th>Разрешить</th>
              <th>Запретить</th>
              <th>Наследовать</th>
            </tr>
          </thead>
          <tbody>
            {grants.map((g) => (
              <tr key={g.article_id}>
                <td>{g.title}</td>
                <td>{g.access_level}</td>
                <td>{g.base_accessible ? "да" : "нет"}</td>
                <td>
                  <input
                    type="radio"
                    name={`grant-${g.article_id}`}
                    checked={g.is_allowed === true}
                    disabled={!canEdit || !g.grantor_can_assign}
                    onChange={() =>
                      setGrants((prev) =>
                        prev.map((x) => (x.article_id === g.article_id ? { ...x, is_allowed: true } : x))
                      )
                    }
                  />
                </td>
                <td>
                  <input
                    type="radio"
                    name={`grant-${g.article_id}`}
                    checked={g.is_allowed === false}
                    disabled={!canEdit || !g.grantor_can_assign}
                    onChange={() =>
                      setGrants((prev) =>
                        prev.map((x) => (x.article_id === g.article_id ? { ...x, is_allowed: false } : x))
                      )
                    }
                  />
                </td>
                <td>
                  <input
                    type="radio"
                    name={`grant-${g.article_id}`}
                    checked={g.is_allowed === null}
                    disabled={!canEdit || !g.grantor_can_assign}
                    onChange={() =>
                      setGrants((prev) =>
                        prev.map((x) => (x.article_id === g.article_id ? { ...x, is_allowed: null } : x))
                      )
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {canEdit ? (
        <button type="button" className="btn btn-secondary" disabled={saving || !selectedId} onClick={onSaveGrants}>
          Сохранить KB
        </button>
      ) : null}

      <h3 className="settings-section-title">Журнал изменений</h3>
      <ul className="access-audit-list">
        {audit.length === 0 ? (
          <li className="muted">Записей пока нет</li>
        ) : (
          audit.map((entry) => (
            <li key={entry.id}>
              <span className="access-audit-date">{new Date(entry.created_at).toLocaleString("ru-RU")}</span>
              {" — "}
              {entry.actor.full_name}: {entry.module} {entry.old_level} → {entry.new_level}
            </li>
          ))
        )}
      </ul>
    </SettingsPanelShell>
  );
}
