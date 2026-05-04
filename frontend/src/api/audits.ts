import { api } from "./client";
import type { Audit, AuditConfig, AuditStatus } from "@/types";

export async function createAudit(payload: {
  dataset_id: string;
  name: string;
  description?: string;
  config: AuditConfig;
}) {
  const { data } = await api.post<Audit>("/api/v1/audits", payload);
  return data;
}

export async function listAudits() {
  const { data } = await api.get<Audit[]>("/api/v1/audits");
  return data;
}

export async function getAudit(id: string) {
  const { data } = await api.get<Audit>(`/api/v1/audits/${id}`);
  return data;
}

export async function getAuditStatus(id: string) {
  const { data } = await api.get<AuditStatus>(`/api/v1/audits/${id}/status`);
  return data;
}
