import type { Audit } from "@/types";
import AuditCard from "./AuditCard";

interface Props {
  audits: Audit[];
  emptyState?: React.ReactNode;
  isLoading?: boolean;
}

export default function AuditHistory({ audits, emptyState, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card animate-pulse h-28" />
        ))}
      </div>
    );
  }

  if (!audits.length) {
    return (
      <div className="card text-center py-10 text-muted">
        {emptyState ?? "No audits yet. Start a new audit to see results here."}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {audits.map((a) => (
        <AuditCard key={a.id} audit={a} />
      ))}
    </div>
  );
}
