import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listDatasets, getDataset, getDatasetPreview, uploadDataset } from "@/api/datasets";
import { api } from "@/api/client";

export function useDatasets() {
  return useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
}

export function useDataset(id: string | undefined) {
  return useQuery({
    queryKey: ["dataset", id],
    queryFn: () => getDataset(id!),
    enabled: !!id,
  });
}

export function useDatasetPreview(id: string | undefined, n = 20) {
  return useQuery({
    queryKey: ["dataset-preview", id, n],
    queryFn: () => getDatasetPreview(id!, n),
    enabled: !!id,
  });
}

export function useUploadDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, name, description }: { file: File; name?: string; description?: string }) =>
      uploadDataset(file, name, description),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

export function useDeleteDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/datasets/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}
