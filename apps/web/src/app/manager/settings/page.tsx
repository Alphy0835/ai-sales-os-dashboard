"use client";

import { useState } from "react";
import { QualityCriteriaSettingsView } from "@/components/QualityCriteriaSettings";
import { KnowledgeBaseSettingsView } from "@/components/KnowledgeBaseSettings";
import { CustomReportsSettingsView } from "@/components/CustomReportsSettings";

type SettingsTab = "criteria" | "knowledge" | "custom-reports";

export default function ManagerSettingsPage() {
  const [tab, setTab] = useState<SettingsTab>("criteria");

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
        </div>
      </header>

      <div className="card card-pad settings-panel">
        {tab === "criteria" && <QualityCriteriaSettingsView />}
        {tab === "knowledge" && <KnowledgeBaseSettingsView />}
        {tab === "custom-reports" && <CustomReportsSettingsView />}
      </div>
    </div>
  );
}
