import { useEffect, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, FileText, Loader2, AlertTriangle } from "lucide-react";
import { downloadReport } from "@/api/reports";

import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

// Use the worker shipped inside the bundled `pdfjs-dist` (no CDN dependency).
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

interface Props {
  auditId: string;
  ready: boolean;
}

/** True PDF preview using react-pdf, with page navigation. */
export default function ReportPreview({ auditId, ready }: Props) {
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [numPages, setNumPages] = useState<number>(0);

  useEffect(() => {
    if (!ready) return;
    let active = true;
    setError(null);
    setBlob(null);
    setPageNumber(1);
    downloadReport(auditId)
      .then((b) => {
        if (active) setBlob(b);
      })
      .catch((e) => {
        if (active) setError(e instanceof Error ? e.message : "Failed to load preview");
      });
    return () => {
      active = false;
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

  if (!blob) {
    return (
      <div className="card flex items-center gap-3 text-sm text-muted">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading preview…
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-bg/40">
        <div className="text-sm">
          Page <span className="font-mono">{pageNumber}</span> of <span className="font-mono">{numPages || "?"}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
            className="btn-ghost py-1 px-2 text-xs"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setPageNumber((p) => Math.min(numPages || p, p + 1))}
            disabled={!numPages || pageNumber >= numPages}
            className="btn-ghost py-1 px-2 text-xs"
            aria-label="Next page"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      <div className="overflow-auto max-h-[720px] p-4 bg-bg flex justify-center">
        <Document
          file={blob}
          onLoadSuccess={({ numPages: n }) => setNumPages(n)}
          loading={<Loader2 className="w-5 h-5 animate-spin text-accent" />}
          error={<span className="text-danger text-sm">Could not render PDF.</span>}
        >
          <Page
            pageNumber={pageNumber}
            renderTextLayer
            renderAnnotationLayer
            width={Math.min(720, window.innerWidth - 80)}
          />
        </Document>
      </div>
    </div>
  );
}
