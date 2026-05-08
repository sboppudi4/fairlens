import { useState } from "react";
import { ChevronDown, ChevronRight, ShieldCheck } from "lucide-react";
import type { AuditResults } from "@/types";

interface Props {
  regulatory: AuditResults["regulatory"];
}

const STATUS_BADGE: Record<string, string> = {
  compliant: "badge-pass",
  partial: "badge-warn",
  non_compliant: "badge-fail",
};

export default function RegulatoryMap({ regulatory }: Props) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {regulatory.frameworks.map((fw) => (
          <FrameworkCard key={fw.framework} fw={fw} />
        ))}
      </div>

      <details className="card">
        <summary className="cursor-pointer font-medium text-sm flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-accent" />
          Clause-level mapping ({regulatory.per_metric.length})
        </summary>
        <ul className="mt-3 space-y-3 text-sm">
          {regulatory.per_metric.map((item, i) => (
            <ClauseEntry key={i} item={item} />
          ))}
        </ul>
      </details>

      {regulatory.cross_cutting.length > 0 && (
        <details className="card">
          <summary className="cursor-pointer font-medium text-sm">
            Cross-cutting clauses ({regulatory.cross_cutting.length})
          </summary>
          <ul className="mt-3 space-y-3 text-sm">
            {regulatory.cross_cutting.map((item, i) => (
              <li key={i} className="border-l-2 pl-3 border-border">
                <div className="text-xs text-muted font-mono">
                  {item.framework} · {item.locator}
                </div>
                <div className="font-medium">{item.title}</div>
                <blockquote className="text-muted italic mt-1">"{item.quote}"</blockquote>
                <div className="mt-1 text-xs">{item.rationale}</div>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function FrameworkCard({ fw }: { fw: AuditResults["regulatory"]["frameworks"][number] }) {
  return (
    <div className="card">
      <div className="font-medium">{fw.framework}</div>
      <div className="font-mono text-3xl mt-1">{fw.compliance_percentage.toFixed(0)}%</div>
      <div className="text-xs text-muted">
        {fw.compliant} of {fw.total} clauses compliant
      </div>
      <div className="mt-3">
        <span className={STATUS_BADGE[fw.status] ?? "badge-warn"}>
          {fw.status.replace(/_/g, " ")}
        </span>
      </div>
    </div>
  );
}

function ClauseEntry({ item }: { item: AuditResults["regulatory"]["per_metric"][number] }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="border-l-2 pl-3 border-border">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="text-left w-full"
      >
        <div className="text-xs text-muted font-mono flex items-center gap-1">
          {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          {item.framework} · {item.locator} · attr <span className="text-fg">{item.sensitive_attribute}</span> ·{" "}
          <span
            className={item.status === "compliant" ? "text-success" : "text-danger"}
          >
            {item.status.replace(/_/g, " ")}
          </span>
        </div>
        <div className="font-medium">{item.title}</div>
      </button>
      {open && (
        <div className="mt-1">
          <blockquote className="text-muted italic">"{item.quote}"</blockquote>
          <div className="mt-1 text-xs">{item.rationale}</div>
          {item.action_required && (
            <div className="mt-1 text-warning text-xs">⚑ {item.action_required}</div>
          )}
        </div>
      )}
    </li>
  );
}
