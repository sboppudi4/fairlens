import { motion } from "framer-motion";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

const STAGES: { key: string; label: string; minProgress: number }[] = [
  { key: "load", label: "Loading dataset", minProgress: 5 },
  { key: "parse", label: "Parsing CSV", minProgress: 30 },
  { key: "metrics", label: "Computing fairness metrics", minProgress: 50 },
  { key: "shap", label: "Running SHAP analysis", minProgress: 70 },
  { key: "regulatory", label: "Mapping to regulations", minProgress: 82 },
  { key: "mitigation", label: "Generating mitigations", minProgress: 88 },
  { key: "finalize", label: "Finalizing results", minProgress: 95 },
];

interface Props {
  progress: number;
  stage?: string | null;
  status: "pending" | "running" | "completed" | "failed";
  errorMessage?: string | null;
}

export default function AuditProgress({ progress, stage, status, errorMessage }: Props) {
  const safeProgress = Math.max(0, Math.min(100, progress));
  return (
    <div className="card space-y-5">
      <div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-muted">{stage ?? statusLabel(status)}</span>
          <span className="font-mono">{safeProgress}%</span>
        </div>
        <div className="h-2 bg-bg rounded overflow-hidden">
          <motion.div
            className={`h-2 rounded ${status === "failed" ? "bg-danger" : "bg-accent"}`}
            initial={{ width: 0 }}
            animate={{ width: `${safeProgress}%` }}
            transition={{ duration: 0.3 }}
            role="progressbar"
            aria-valuenow={safeProgress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      <ol className="space-y-2">
        {STAGES.map((s) => {
          const reached = safeProgress >= s.minProgress;
          const active = !reached && nextActive(safeProgress, s.minProgress);
          return (
            <li key={s.key} className="flex items-center gap-3 text-sm">
              {reached ? (
                <CheckCircle2 className="w-4 h-4 text-success" />
              ) : active ? (
                <Loader2 className="w-4 h-4 text-accent animate-spin" />
              ) : (
                <Circle className="w-4 h-4 text-muted/40" />
              )}
              <span
                className={
                  reached ? "text-fg" : active ? "text-accent" : "text-muted/60"
                }
              >
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>

      {status === "failed" && errorMessage && (
        <div role="alert" className="text-sm text-danger font-mono break-all">
          {errorMessage}
        </div>
      )}
    </div>
  );
}

function statusLabel(status: Props["status"]): string {
  switch (status) {
    case "pending":
      return "Queued";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
  }
}

function nextActive(progress: number, threshold: number): boolean {
  const lower = STAGES.filter((s) => s.minProgress <= progress);
  const next = STAGES[lower.length];
  return next?.minProgress === threshold;
}
