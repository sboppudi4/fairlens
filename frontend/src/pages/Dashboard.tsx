import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { listAudits } from "@/api/audits";
import { listDatasets } from "@/api/datasets";
import AuditHistory from "@/components/audit/AuditHistory";

export default function Dashboard() {
  const audits = useQuery({ queryKey: ["audits"], queryFn: listAudits, refetchInterval: 5000 });
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });

  // The list endpoint returns AuditOut without nested results. "Completed" count is exact;
  // a passing-rate badge would require fetching each audit's detail (deferred).
  const all = audits.data ?? [];
  const completed = all.filter((a) => a.status === "completed").length;
  const failed = all.filter((a) => a.status === "failed").length;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted text-sm">Recent audits and datasets.</p>
        </div>
        <Link to="/audits/new" className="btn-primary">
          <Plus className="w-4 h-4" />
          New audit
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Stat label="Audits" value={audits.data?.length ?? "—"} />
        <Stat label="Completed" value={completed} />
        <Stat label="Failed" value={failed} tone={failed > 0 ? "danger" : undefined} />
        <Stat label="Datasets" value={datasets.data?.length ?? "—"} />
      </div>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Recent audits</h2>
        </div>
        <AuditHistory
          audits={all}
          isLoading={audits.isLoading}
          emptyState={
            <div>
              <p className="text-sm mb-4">No audits yet.</p>
              <Link to="/audits/new" className="btn-primary inline-flex">
                Run your first audit
              </Link>
            </div>
          }
        />
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | string;
  tone?: "danger";
}) {
  const cls = tone === "danger" ? "text-danger" : "text-fg";
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wider text-muted">{label}</div>
      <div className={`font-mono text-3xl font-semibold mt-1 ${cls}`}>{value}</div>
    </div>
  );
}
