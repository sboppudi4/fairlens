import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { MetricResult } from "@/types";
import { humanizeMetricName } from "@/utils/formatters";

const SEV: Record<string, { border: string; badge: string }> = {
  pass: { border: "border-success/40", badge: "badge-pass" },
  warning: { border: "border-warning/40", badge: "badge-warn" },
  fail: { border: "border-danger/40", badge: "badge-fail" },
};

export default function MetricCard({ metric }: { metric: MetricResult }) {
  const [showDetail, setShowDetail] = useState(false);
  const sev = SEV[metric.severity] ?? SEV.fail;
  return (
    <div className={`card ${sev.border}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-sm text-muted font-mono">{humanizeMetricName(metric.name)}</div>
          <div className="font-mono text-3xl font-semibold mt-1">{metric.value.toFixed(4)}</div>
          <div className="text-xs text-muted">threshold {metric.threshold}</div>
        </div>
        <span className={sev.badge}>{metric.severity}</span>
      </div>
      <p className="text-xs text-muted mt-3">{metric.interpretation}</p>
      <button
        type="button"
        onClick={() => setShowDetail((v) => !v)}
        className="mt-2 text-xs text-muted hover:text-fg flex items-center gap-1"
        aria-expanded={showDetail}
      >
        {showDetail ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        per-group breakdown
      </button>
      {showDetail && metric.per_group && (
        <pre className="font-mono text-xs mt-2 bg-bg p-2 rounded overflow-auto max-h-48">
          {JSON.stringify(metric.per_group, null, 2)}
        </pre>
      )}
    </div>
  );
}
