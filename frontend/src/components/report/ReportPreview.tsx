import { useEffect, useState } from "react";
import { FileText, Loader2, AlertTriangle } from "lucide-react";
import { downloadReport } from "@/api/reports";

interface Props {
  auditId: string;
  ready: boolean;
}

/** Inline iframe preview of the PDF report once it's available. */
export default function ReportPreview({ auditId, ready }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    let active = true;
    let createdUrl: string | null = null;
    setError(null);
    downloadReport(auditId)
      .then((blob) => {
        if (!active) return;
        createdUrl = URL.createObjectURL(blob);
        setUrl(createdUrl);
      })
      .catch((e) => {
        if (active) setError(e instanceof Error ? e.message : "Failed to load preview");
      });
    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [auditId, ready]);

  if (!ready) {
    return (
      <div className="card flex items-center gap-3 text-sm text-muted">
        <FileText className="w-5 h-5 text-accent" />
        Report has not been generated yet.
      </div>
    );
  }

  if (error) {
    return (
      <div className="card flex items-center gap-3 text-sm text-danger" role="alert">
        <AlertTriangle className="w-5 h-5" />
        {error}
      </div>
    );
  }

  if (!url) {
    return (
      <div className="card flex items-center gap-3 text-sm text-muted">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading preview…
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden">
      <iframe
        src={`${url}#toolbar=0&navpanes=0`}
        title="FairLens audit report preview"
        className="w-full h-[720px] border-0"
      />
    </div>
  );
}
