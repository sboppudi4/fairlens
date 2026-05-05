import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { listAudits } from "@/api/audits";
import { listDatasets } from "@/api/datasets";

export default function Dashboard() {
  const audits = useQuery({ queryKey: ["audits"], queryFn: listAudits, refetchInterval: 5000 });
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });

  // Note: list endpoint returns AuditOut (no results); the Dashboard counts only "completed"
  // here. A full pass count would require fetching each audit's detail, deferred to Phase 2.
  const completed = (audits.data ?? []).filter((a) => a.status === "completed").length;

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

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Stat label="Audits" value={audits.data?.length ?? "—"} />
        <Stat label="Completed" value={completed} />
        <Stat label="Datasets" value={datasets.data?.length ?? "—"} />
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Recent audits</h2>
        <div className="card !p-0 overflow-hidden">
          {audits.isLoading ? (
            <div className="p-6 text-muted text-sm">Loading…</div>
          ) : !audits.data || audits.data.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-muted text-sm mb-4">No audits yet.</p>
              <Link to="/audits/new" className="btn-primary">
                Run your first audit
              </Link>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-bg/40 border-b border-border">
                <tr className="text-left text-muted">
                  <th className="px-4 py-2 font-medium">Name</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Created</th>
                  <th className="px-4 py-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {audits.data.map((a) => (
                  <tr key={a.id} className="border-b border-border/50 last:border-0">
                    <td className="px-4 py-3">
                      <div className="font-medium">{a.name}</div>
                      <div className="text-xs text-muted">{a.config.sensitive_attributes.join(", ")}</div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="px-4 py-3 text-muted">{new Date(a.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      <Link to={`/audits/${a.id}`} className="text-accent hover:underline">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wider text-muted">{label}</div>
      <div className="font-mono text-3xl font-semibold mt-1">{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "completed"
      ? "badge-pass"
      : status === "running"
      ? "badge-warn"
      : status === "failed"
      ? "badge-fail"
      : "badge-neutral";
  return <span className={cls}>{status}</span>;
}
