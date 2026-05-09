import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAudit, getAuditStatus } from "@/api/audits";
import ShapPanel from "@/components/results/ShapPanel";
import MitigationPanel from "@/components/results/MitigationPanel";
import DownloadButton from "@/components/report/DownloadButton";
import FairnessGauge from "@/components/results/FairnessGauge";
import MetricCard from "@/components/results/MetricCard";
import BiasHeatmap from "@/components/results/BiasHeatmap";
import ShapWaterfall from "@/components/results/ShapWaterfall";
import RegulatoryMap from "@/components/results/RegulatoryMap";
import Sidebar from "@/components/layout/Sidebar";
import AuditProgress from "@/components/audit/AuditProgress";

const SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "metrics", label: "Metrics summary" },
  { id: "heatmap", label: "Bias heat-map" },
  { id: "deep-dive", label: "Per-attribute detail" },
  { id: "shap", label: "SHAP explainability" },
  { id: "regulatory", label: "Regulatory mapping" },
  { id: "mitigations", label: "Mitigations" },
];

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
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold">{a.name}</h2>
        <AuditProgress
          progress={status.data?.progress ?? 0}
          stage={status.data?.stage ?? null}
          status={a.status}
        />
        <p className="text-xs text-muted">Polling every 2 seconds…</p>
      </div>
    );
  }

  if (a.status === "failed") {
    return (
      <div className="max-w-2xl mx-auto">
        <AuditProgress
          progress={0}
          status="failed"
          stage="Audit failed"
          errorMessage={a.error_message}
        />
      </div>
    );
  }

  const r = a.results;
  if (!r) return <div className="text-muted">No results.</div>;

  const allMetricEntries = Object.entries(r.sensitive_attributes).flatMap(([attr, block]) =>
    Object.entries(block.metrics).map(([key, m]) => ({ attr, key, m })),
  );

  return (
    <div className="flex gap-8">
      <Sidebar links={SECTIONS} />
      <div className="flex-1 space-y-10 min-w-0">
        <section id="overview">
          <header className="card">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h1 className="text-2xl font-bold">{a.name}</h1>
                <p className="text-sm text-muted">
                  {r.dataset.row_count.toLocaleString()} rows ·{" "}
                  {new Date(r.completed_at).toLocaleString()}
                </p>
                {a.description && (
                  <p className="text-sm text-muted mt-2 max-w-prose">{a.description}</p>
                )}
              </div>
              <div className="flex items-center gap-6">
                <FairnessGauge
                  score={r.summary.overall_fairness_score}
                  riskLevel={r.summary.risk_level}
                />
                <DownloadButton auditId={a.id} />
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
              <Stat
                label="Metrics passing"
                value={`${r.summary.metrics_passing} / ${r.summary.metrics_total}`}
              />
              <Stat label="Failures" value={r.summary.severities.fail} tone="danger" />
              <Stat label="Warnings" value={r.summary.severities.warning} tone="warning" />
              <Stat label="Sensitive attrs" value={Object.keys(r.sensitive_attributes).length} />
            </div>
          </header>
        </section>

        <section id="metrics" className="space-y-3">
          <h2 className="text-lg font-semibold">Metrics summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {allMetricEntries.slice(0, 8).map(({ attr, key, m }) => (
              <div key={`${attr}-${key}`}>
                <div className="text-[10px] uppercase tracking-wider text-muted mb-1">{attr}</div>
                <MetricCard metric={m} />
              </div>
            ))}
          </div>
        </section>

        <section id="heatmap" className="space-y-3">
          <h2 className="text-lg font-semibold">Bias heat-map</h2>
          <BiasHeatmap sensitiveAttributes={r.sensitive_attributes} />
        </section>

        <section id="deep-dive" className="space-y-6">
          <h2 className="text-lg font-semibold">Per-attribute detail</h2>
          {Object.entries(r.sensitive_attributes).map(([attr, block]) => (
            <div key={attr} className="space-y-3">
              <h3 className="font-medium">
                Sensitive attribute: <span className="font-mono text-accent">{attr}</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(block.metrics).map(([key, m]) => (
                  <MetricCard key={key} metric={m} />
                ))}
              </div>
              <PerGroupTable perGroup={block.per_group_performance} />
            </div>
          ))}
        </section>

        <section id="shap" className="space-y-4">
          <ShapPanel shap={r.shap} />
          {r.shap?.available && r.shap.feature_importance && (
            <ShapWaterfall features={r.shap.feature_importance} />
          )}
        </section>

        <section id="regulatory" className="space-y-3">
          <h2 className="text-lg font-semibold">Regulatory compliance</h2>
          <RegulatoryMap regulatory={r.regulatory} />
        </section>

        <section id="mitigations">
          <MitigationPanel mitigations={r.mitigations} />
        </section>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: "danger" | "warning";
}) {
  const cls = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : "text-fg";
  return (
    <div>
      <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
      <div className={`font-mono text-2xl font-semibold ${cls}`}>{value}</div>
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
