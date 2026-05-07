import { Download, FileText, Loader2 } from "lucide-react";
import { useGenerateReport, useDownloadReport, useReportStatus } from "@/hooks/useReport";

export default function DownloadButton({ auditId }: { auditId: string }) {
  const status = useReportStatus(auditId);
  const generate = useGenerateReport(auditId);
  const download = useDownloadReport(auditId);

  const ready = status.data?.ready;
  const progress = status.data?.progress ?? 0;
  const stage = status.data?.stage ?? null;

  if (status.isLoading && !status.data) {
    return (
      <button className="btn-primary opacity-60" disabled>
        <Loader2 className="w-4 h-4 animate-spin" /> Loading…
      </button>
    );
  }

  if (ready) {
    return (
      <button
        onClick={() => download.mutate()}
        className="btn-primary"
        disabled={download.isPending}
        aria-label="Download PDF report"
      >
        {download.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
        Download report
      </button>
    );
  }

  if (progress > 0 && progress < 100) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <Loader2 className="w-4 h-4 animate-spin text-accent" />
        <div className="flex flex-col">
          <span className="font-medium">Building report — {progress}%</span>
          {stage && <span className="text-muted text-xs">{stage}</span>}
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={() => generate.mutate()}
      className="btn-primary"
      disabled={generate.isPending}
    >
      {generate.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
      Generate PDF report
    </button>
  );
}
