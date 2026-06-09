import { authFetch } from "./api";

export type KnowledgeArticle = {
  id: string;
  title: string;
  category: string;
  category_label: string;
  content: string;
  tags: string;
  access_level: string;
  access_label: string;
  is_active: boolean;
};

export type AgentMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Array<{ id: string; title: string; category: string; excerpt: string }>;
  created_at: string;
};

export type AgentSession = {
  id: string;
  client_name: string;
  client_note: string;
  messages: AgentMessage[];
};

export function fetchKnowledgeArticles(): Promise<{ count: number; results: KnowledgeArticle[] }> {
  return authFetch("/api/v1/manager/settings/knowledge/");
}

export function createKnowledgeArticle(payload: Partial<KnowledgeArticle>): Promise<KnowledgeArticle> {
  return authFetch("/api/v1/manager/settings/knowledge/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteKnowledgeArticle(id: string): Promise<void> {
  return authFetch(`/api/v1/manager/settings/knowledge/${id}/`, { method: "DELETE" });
}

export function sendAgentMessage(
  variant: "manager" | "employee",
  payload: { message: string; session_id?: string; client_name?: string; client_note?: string },
): Promise<AgentSession> {
  const path = variant === "manager" ? "/api/v1/manager/agent/chat/" : "/api/v1/employee/agent/chat/";
  return authFetch(path, { method: "POST", body: JSON.stringify(payload) });
}
