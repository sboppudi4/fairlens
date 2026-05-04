import { api } from "./client";
import type { Dataset } from "@/types";

export async function listDatasets() {
  const { data } = await api.get<Dataset[]>("/api/v1/datasets");
  return data;
}

export async function getDataset(id: string) {
  const { data } = await api.get<Dataset>(`/api/v1/datasets/${id}`);
  return data;
}

export async function uploadDataset(file: File, name?: string, description?: string) {
  const fd = new FormData();
  fd.append("file", file);
  if (name) fd.append("name", name);
  if (description) fd.append("description", description);
  const { data } = await api.post<Dataset>("/api/v1/datasets/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getDatasetPreview(id: string, n = 20) {
  const { data } = await api.get<{ columns: string[]; rows: Record<string, unknown>[]; row_count: number }>(
    `/api/v1/datasets/${id}/preview`,
    { params: { n } }
  );
  return data;
}
