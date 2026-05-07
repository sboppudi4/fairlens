import { Link } from "react-router-dom";
import { Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import type { Audit } from "@/types";
import { formatRelativeTime } from "@/utils/formatters";

const ICONS = {
  pending: <Clock className="w-4 h-4 text-muted" />,
  running: <Loader2 className="w-4 h-4 text-accent animate-spin" />,
  completed: <CheckCircle2 className="w-4 h-4 text-success" />,
  failed: <XCircle className="w-4 h-4 text-danger" />,
} as const;

const BADGES: Record<Audit["status"], string> = {
  pending: "badge-warn",
  running: "badge-warn",
  completed: "badge-pass",
  failed: "badge-fail",
};

export default function AuditCard({ audit }: { audit: Audit }) {
  return (
    <Link
      to={`/audits/${audit.id}`}
      className="card hover:border-accent/60 transition-colors block"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-medium truncate">{audit.name}</div>
          <div className="text-xs text-muted mt-1">
            Created {formatRelativeTime(audit.created_at)}
          </div>
          {audit.description && (
            <p className="text-xs text-muted mt-2 line-clamp-2">{audit.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {ICONS[audit.status]}
          <span className={BADGES[audit.status]}>{audit.status}</span>
        </div>
      </div>
      {audit.results && (
        <div className="mt-3 pt-3 border-t border-border/50 flex items-center justify-between text-xs">
          <span className="text-muted">Fairness score</span>
          <span className="font-mono font-bold">
            {audit.results.summary.overall_fairness_score.toFixed(0)}
          </span>
        </div>
      )}
    </Link>
  );
}
