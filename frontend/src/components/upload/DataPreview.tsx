interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount?: number;
  maxRows?: number;
}

export default function DataPreview({ columns, rows, rowCount, maxRows = 20 }: Props) {
  const visible = rows.slice(0, maxRows);
  return (
    <div className="card p-0 overflow-hidden">
      <div className="px-4 py-2 flex items-center justify-between border-b border-border">
        <div className="text-sm font-medium">Data preview</div>
        <div className="text-xs text-muted">
          showing {visible.length} of {rowCount?.toLocaleString() ?? rows.length} rows
        </div>
      </div>
      <div className="overflow-auto max-h-96">
        <table className="w-full text-xs font-mono">
          <thead className="sticky top-0 bg-surface text-muted">
            <tr>
              {columns.map((c) => (
                <th key={c} className="px-3 py-2 text-left border-b border-border whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((row, i) => (
              <tr key={i} className="border-b border-border/40 hover:bg-bg/40">
                {columns.map((c) => (
                  <td key={c} className="px-3 py-1.5 whitespace-nowrap">
                    {formatCell(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return Number.isInteger(v) ? v.toString() : v.toFixed(4);
  return String(v);
}
