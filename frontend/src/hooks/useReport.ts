import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { downloadReport, generateReport, getReportStatus } from "@/api/reports";

export function useReportStatus(auditId: string, enabled = true) {
  return useQuery({
    queryKey: ["report-status", auditId],
    queryFn: () => getReportStatus(auditId),
    enabled,
    refetchInterval: (q) => {
      const data = q.state.data;
      if (!data) return 2000;
      return data.ready ? false : 2000;
    },
  });
}

export function useGenerateReport(auditId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => generateReport(auditId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-status", auditId] });
    },
  });
}

export function useDownloadReport(auditId: string, fileName?: string) {
  return useMutation({
    mutationFn: async () => {
      const blob = await downloadReport(auditId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName || `fairlens-audit-${auditId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  });
}
