import { useState } from "react";
import { ChevronDown, ChevronRight, Lightbulb } from "lucide-react";
import type { AuditResults } from "@/types";

const COMPLEXITY_BADGE: Record<string, string> = {
  low: "badge-pass",
  medium: "badge-warn",
  high: "badge-fail",
};

export default function MitigationPanel({
  mitigations,
}: {
  mitigations?: AuditResults["mitigations"];
}) {
  if (!mitigations || mitigations.length === 0) {
    return (
      <section>
        <h2 className="text-lg font-semibold mb-3">Mitigation recommendations</h2>
        <div className="card text-sm text-muted">
          All evaluated metrics pass at the configured thresholds — no mitigations needed at this time.
          Continue monitoring via scheduled FairLens audits.
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold flex items-center gap-2">
        <Lightbulb className="w-5 h-5 text-accent" /> Mitigation recommendations
      </h2>
      <div className="space-y-3">
        {mitigations.map((m, i) => (
          <MitigationCard key={i} m={m} />
        ))}
      </div>
    </section>
  );
}

function MitigationCard({ m }: { m: NonNullable<AuditResults["mitigations"]>[number] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card">
      <button
        type="button"
        className="w-full flex items-start justify-between gap-3 text-left"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold">{m.technique}</span>
            <span className={COMPLEXITY_BADGE[m.complexity] ?? "badge-warn"}>{m.complexity}</span>
          </div>
          <div className="text-xs text-muted mt-1">
            <span className="font-mono">{m.failing_metric.replace(/_/g, " ")}</span>
            {" · attr "}
            <span className="font-mono">{m.sensitive_attribute}</span>
            {m.metric_value !== null && (
              <>
                {" · value "}
                <span className="font-mono">{m.metric_value.toFixed(4)}</span>
              </>
            )}
          </div>
        </div>
        {open ? <ChevronDown className="w-4 h-4 text-muted" /> : <ChevronRight className="w-4 h-4 text-muted" />}
      </button>
      {open && (
        <div className="mt-4 space-y-3">
          <p className="text-sm">{m.description}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div>
              <div className="text-muted">Expected improvement</div>
              <div>{m.expected_improvement}</div>
            </div>
            <div>
              <div className="text-muted">Reference</div>
              <div>{m.reference}</div>
            </div>
          </div>
          {m.flagged_features && m.flagged_features.length > 0 && (
            <div className="text-xs">
              <div className="text-muted mb-1">Flagged proxy features</div>
              <ul className="font-mono list-disc pl-5">
                {m.flagged_features.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
          <pre className="font-mono text-xs bg-bg p-3 rounded border border-border overflow-auto">
            {m.code_snippet}
          </pre>
        </div>
      )}
    </div>
  );
}
