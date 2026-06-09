"use client";

import { useEffect, useState } from "react";
import { AccessSettingsView } from "@/components/AccessSettings";
import { QualityCriteriaSettingsView } from "@/components/QualityCriteriaSettings";
import { KnowledgeBaseSettingsView } from "@/components/KnowledgeBaseSettings";
import { CustomReportsSettingsView } from "@/components/CustomReportsSettings";
import { getStoredPermissions } from "@/lib/auth";

type SettingsTab = "criteria" | "knowledge" | "custom-reports" | "access";

export default function ManagerSettingsPage() {
  const [tab, setTab] = useState<SettingsTab>("criteria");
  const [showAccessTab, setShowAccessTab] = useState(true);

  useEffect(() => {
    const permissions = getStoredPermissions();
    if (permissions && permissions.settings === "none") {
      setShowAccessTab(false);
      setTab((current) => (current === "access" ? "criteria" : current));
    }
  }, []);

  return (
    <div className="manager-main">
      <header className="settings-header">
        <h1 className="page-title">Настройки</h1>
        <div className="chips">
          <button type="button" className={`chip${tab === "criteria" ? " on" : ""}`} onClick={() => setTab("criteria")}>
            Критерии качества
          </button>
          <button type="button" className={`chip${tab === "knowledge" ? " on" : ""}`} onClick={() => setTab("knowledge")}>
            База знаний
          </button>
          <button
            type="button"
            className={`chip${tab === "custom-reports" ? " on" : ""}`}
            onClick={() => setTab("custom-reports")}
          >
            Кастомные отчёты
          </button>
          {showAccessTab && (
            <button type="button" className={`chip${tab === "access" ? " on" : ""}`} onClick={() => setTab("access")}>
              Права доступа
            </button>
          )}
        </div>
      </header>

      <div className="card card-pad settings-panel">
        {tab === "criteria" && <QualityCriteriaSettingsView />}
        {tab === "knowledge" && <KnowledgeBaseSettingsView />}
        {tab === "custom-reports" && <CustomReportsSettingsView />}
        {tab === "access" && showAccessTab && <AccessSettingsView />}
      </div>
    </div>
  );
}
