"use client";

import { useState } from "react";

type AddPanelProps = {
  label: string;
  canEdit: boolean;
  onSubmit: (e: React.FormEvent) => void | Promise<void>;
  children: React.ReactNode;
};

export function SettingsPanelShell({
  children,
  footer,
}: {
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div className="settings-panel-inner">
      <div className="settings-panel-body">{children}</div>
      {footer ? <div className="settings-panel-footer">{footer}</div> : null}
    </div>
  );
}

export function SettingsAddPanel({ label, canEdit, onSubmit, children }: AddPanelProps) {
  const [open, setOpen] = useState(false);

  if (!canEdit) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(e);
    setOpen(false);
  };

  return (
    <>
      {!open ? (
        <button type="button" className="settings-add-btn" onClick={() => setOpen(true)} aria-label={label}>
          +
        </button>
      ) : (
        <form className="settings-add-form" onSubmit={handleSubmit}>
          <div className="settings-add-head">
            <h3>{label}</h3>
            <button type="button" className="settings-add-btn settings-add-btn-close" onClick={() => setOpen(false)} aria-label="Закрыть">
              −
            </button>
          </div>
          {children}
          <div className="settings-add-actions">
            <button type="submit" className="btn btn-primary">
              Сохранить
            </button>
          </div>
        </form>
      )}
    </>
  );
}
