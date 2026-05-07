import { api } from "./client";
import type { ReportStatus } from "@/types";

export async function generateReport(auditId: string) {
  const { data } = await api.post<{ audit_id: string; task_id: string; status: string }>(
    `/api/v1/reports/${auditId}/generate`,
  );
  return data;
}

export async function getReportStatus(auditId: string) {
  const { data } = await api.get<ReportStatus>(`/api/v1/reports/${auditId}/status`);
  return data;
}

export function downloadReportUrl(auditId: string) {
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://localhost:8000";
  return `${base}/api/v1/reports/${auditId}/download`;
}

export async function downloadReport(auditId: string): Promise<Blob> {
  const { data } = await api.get(`/api/v1/reports/${auditId}/download`, { responseType: "blob" });
  return data as Blob;
}
