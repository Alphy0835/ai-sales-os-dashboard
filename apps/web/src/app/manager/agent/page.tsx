"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AgentChatView } from "@/components/AgentChat";

function ManagerAgentContent() {
  const params = useSearchParams();
  return (
    <AgentChatView
      variant="manager"
      initialClientName={params.get("client_name") ?? ""}
      initialClientNote={params.get("client_note") ?? ""}
    />
  );
}

export default function ManagerAgentPage() {
  return (
    <Suspense fallback={<div className="text-secondary">Загрузка…</div>}>
      <ManagerAgentContent />
    </Suspense>
  );
}
