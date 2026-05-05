import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAudit, getAuditStatus } from "@/api/audits";
import type { MetricResult } from "@/types";
import ShapPanel from "@/components/results/ShapPanel";
import MitigationPanel from "@/components/results/MitigationPanel";
import DownloadButton from "@/components/report/DownloadButton";

export default function AuditResults() {
  const { id = "" } = useParams();

  const audit = useQuery({
    queryKey: ["audit", id],
    queryFn: () => getAudit(id),
    refetchInterval: (q) => {
      const data = q.state.data;
      return data && (data.status === "pending" || data.status === "running") ? 2000 : false;
    },
  });

  const status = useQuery({
    queryKey: ["audit-status", id],
    queryFn: () => getAuditStatus(id),
    enabled: audit.data?.status === "pending" || audit.data?.status === "running",
    refetchInterval: 2000,
  });

  if (audit.isLoading) return <div className="text-muted">Loading…</div>;
  if (audit.error || !audit.data) return <div className="text-danger">Failed to load audit.</div>;

  const a = audit.data;

  if (a.status === "pending" || a.status === "running") {
    const progress = status.data?.progress ?? 0;
    const stage = status.data?.stage ?? "queued";
    return (
      <div className="max-w-2xl mx-auto card space-y-4">
        <h2 className="text-xl font-semibold">{a.name}</h2>
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted">{stage}</span>
            <span className="font-mono">{progress}%</span>
          </div>
          <div className="h-2 bg-bg rounded">
            <div
              className="h-2 bg-accent rounded transition-all"
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-valuenow={progress}
            />
          </div>
        </div>
        <p className="text-sm text-muted">Polling every 2 seconds…</p>
      </div>
    );
  }

  if (a.status === "failed") {
    return (
      <div className="card border-danger/40">
        <h2 className="text-xl font-semibold text-danger">Audit failed</h2>
        <p className="text-sm text-muted mt-2 font-mono">{a.error_message}</p>
      </div>
    );
  }

  const r = a.results;
  if (!r) return <div className="text-muted">No results.</div>;

  return (
    <div className="space-y-8">
      <header className="card">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold">{a.name}</h1>
            <p className="text-sm text-muted">
              {r.dataset.row_count.toLocaleString()} rows · {new Date(r.completed_at).toLocaleString()}
            </p>
          </div>
          <div className="flex items-center gap-6">
            <ScoreGauge score={r.summary.overall_fairness_score} risk={r.summary.risk_level} />
            <DownloadButton auditId={a.id} />
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <Stat label="Metrics passing" value={`${r.summary.metrics_passing} / ${r.summary.metrics_total}`} />
          <Stat label="Failures" value={r.summary.severities.fail} tone="danger" />
          <Stat label="Warnings" value={r.summary.severities.warning} tone="warning" />
          <Stat label="Sensitive attrs" value={Object.keys(r.sensitive_attributes).length} />
        </div>
      </header>

      {Object.entries(r.sensitive_attributes).map(([attr, block]) => (
        <section key={attr} className="space-y-3">
          <h2 className="text-lg font-semibold">
            Sensitive attribute: <span className="font-mono text-accent">{attr}</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(block.metrics).map(([key, m]) => (
              <MetricCard key={key} metric={m} />
            ))}
          </div>
          <PerGroupTable perGroup={block.per_group_performance} />
        </section>
      ))}

      <ShapPanel shap={r.shap} />

      <section>
        <h2 className="text-lg font-semibold mb-3">Regulatory compliance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {r.regulatory.frameworks.map((fw) => (
            <div key={fw.framework} className="card">
              <div className="font-medium">{fw.framework}</div>
              <div className="font-mono text-2xl mt-1">{fw.compliance_percentage}%</div>
              <div className="text-xs text-muted">
                {fw.compliant} compliant / {fw.total} total
              </div>
              <span
                className={
                  fw.status === "compliant" ? "badge-pass mt-3" : fw.status === "partial" ? "badge-warn mt-3" : "badge-fail mt-3"
                }
              >
                {fw.status}
              </span>
            </div>
          ))}
        </div>

        <details className="mt-4 card">
          <summary className="cursor-pointer font-medium text-sm">Show clause-level mapping</summary>
          <ul className="mt-3 space-y-3 text-sm">
            {r.regulatory.per_metric.map((item, i) => (
              <li key={i} className="border-l-2 pl-3 border-border">
                <div className="text-xs text-muted">
                  <span className="font-mono">{item.framework}</span> · {item.locator} · attr{" "}
                  <span className="font-mono">{item.sensitive_attribute}</span> · metric{" "}
                  <span className="font-mono">{item.metric}</span> ·{" "}
                  <span className={item.status === "compliant" ? "text-success" : "text-danger"}>
                    {item.status}
                  </span>
                </div>
                <div className="font-medium">{item.title}</div>
                <blockquote className="text-muted italic mt-1">"{item.quote}"</blockquote>
                <div className="mt-1">{item.rationale}</div>
                {item.action_required && <div className="mt-1 text-warning">⚑ {item.action_required}</div>}
              </li>
            ))}
          </ul>
        </details>
      </section>

      <MitigationPanel mitigations={r.mitigations} />
    </div>
  );
}

function ScoreGauge({ score, risk }: { score: number; risk: string }) {
  const tone =
    risk === "Low Risk" ? "text-success" : risk === "Medium Risk" ? "text-warning" : "text-danger";
  return (
    <div className="text-right">
      <div className={`font-mono text-5xl font-bold ${tone}`}>{score}</div>
      <div className={`text-sm ${tone}`}>{risk}</div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string | number; tone?: "danger" | "warning" }) {
  const cls = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : "text-fg";
  return (
    <div>
      <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
      <div className={`font-mono text-2xl font-semibold ${cls}`}>{value}</div>
    </div>
  );
}

function MetricCard({ metric }: { metric: MetricResult }) {
  const cls =
    metric.severity === "pass" ? "border-success/40" : metric.severity === "warning" ? "border-warning/40" : "border-danger/40";
  const badge =
    metric.severity === "pass" ? "badge-pass" : metric.severity === "warning" ? "badge-warn" : "badge-fail";
  return (
    <div className={`card ${cls}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-sm text-muted font-mono">{metric.name}</div>
          <div className="font-mono text-3xl font-semibold mt-1">{metric.value.toFixed(4)}</div>
          <div className="text-xs text-muted">threshold {metric.threshold}</div>
        </div>
        <span className={badge}>{metric.severity}</span>
      </div>
      <p className="text-xs text-muted mt-3">{metric.interpretation}</p>
      {metric.per_group && (
        <details className="mt-2 text-xs">
          <summary className="cursor-pointer text-muted">per-group breakdown</summary>
          <pre className="font-mono text-xs mt-2 bg-bg p-2 rounded overflow-auto">
            {JSON.stringify(metric.per_group, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function PerGroupTable({ perGroup }: { perGroup: Record<string, Record<string, unknown>> }) {
  const groups = Object.keys(perGroup);
  if (groups.length === 0) return null;
  const cols = ["n", "selection_rate", "accuracy", "precision", "recall", "f1", "tpr", "fpr"];
  return (
    <details className="card">
      <summary className="cursor-pointer text-sm font-medium">Per-group performance</summary>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-sm font-mono">
          <thead className="text-muted text-xs">
            <tr>
              <th className="px-2 py-1 text-left">group</th>
              {cols.map((c) => (
                <th key={c} className="px-2 py-1 text-right">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g} className="border-t border-border/50">
                <td className="px-2 py-1">{g}</td>
                {cols.map((c) => (
                  <td key={c} className="px-2 py-1 text-right">
                    {String((perGroup[g] as Record<string, unknown>)[c] ?? "—")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
