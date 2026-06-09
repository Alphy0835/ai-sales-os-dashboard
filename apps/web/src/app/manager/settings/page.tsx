"use client";

import { useState } from "react";
import { QualityCriteriaSettingsView } from "@/components/QualityCriteriaSettings";
import { KnowledgeBaseSettingsView } from "@/components/KnowledgeBaseSettings";
import { CustomReportsSettingsView } from "@/components/CustomReportsSettings";

export default function ManagerSettingsPage() {
  const [tab, setTab] = useState<"criteria" | "knowledge" | "custom-reports">("criteria");

  return (
    <>
      <header>
        <h1 className="page-title">Настройки</h1>
        <p className="page-subtitle">Критерии качества, база знаний и кастомные отчёты</p>
      </header>
      <div className="chips mb-4">
        <button type="button" className={`chip${tab === "criteria" ? " on" : ""}`} onClick={() => setTab("criteria")}>
          Критерии качества
        </button>
        <button type="button" className={`chip${tab === "knowledge" ? " on" : ""}`} onClick={() => setTab("knowledge")}>
          База знаний
        </button>
        <button type="button" className={`chip${tab === "custom-reports" ? " on" : ""}`} onClick={() => setTab("custom-reports")}>
          Кастомные отчёты
        </button>
      </div>
      {tab === "criteria" && <QualityCriteriaSettingsView />}
      {tab === "knowledge" && <KnowledgeBaseSettingsView />}
      {tab === "custom-reports" && <CustomReportsSettingsView />}
    </>
  );
}
