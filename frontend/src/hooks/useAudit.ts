import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { createAudit, getAudit, getAuditStatus, listAudits } from "@/api/audits";
import { api } from "@/api/client";
import type { AuditConfig } from "@/types";

export function useAudits() {
  return useQuery({
    queryKey: ["audits"],
    queryFn: listAudits,
    refetchInterval: 5000,
  });
}

export function useAudit(id: string | undefined) {
  return useQuery({
    queryKey: ["audit", id],
    queryFn: () => getAudit(id!),
    enabled: !!id,
    refetchInterval: (q) => {
      const data = q.state.data;
      return data && (data.status === "pending" || data.status === "running") ? 2000 : false;
    },
  });
}

export function useAuditStatus(id: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ["audit-status", id],
    queryFn: () => getAuditStatus(id!),
    enabled: !!id && enabled,
    refetchInterval: 2000,
  });
}

export function useCreateAudit() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (input: {
      dataset_id: string;
      name: string;
      description?: string;
      config: AuditConfig;
    }) => createAudit(input),
    onSuccess: (a) => {
      qc.invalidateQueries({ queryKey: ["audits"] });
      navigate(`/audits/${a.id}`);
    },
  });
}

export function useDeleteAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/audits/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["audits"] });
    },
  });
}
