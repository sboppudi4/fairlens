import { useMemo } from "react";
import type { AuditResults, MetricResult } from "@/types";

interface Props {
  sensitiveAttributes: AuditResults["sensitive_attributes"];
}

const METRIC_ORDER = [
  "demographic_parity_difference",
  "disparate_impact_ratio",
  "equal_opportunity_difference",
  "equalized_odds_difference",
  "predictive_parity_difference",
  "calibration_difference",
];

/** Heat-map: rows = sensitive attributes, columns = fairness metrics, cell = severity-coloured value. */
export default function BiasHeatmap({ sensitiveAttributes }: Props) {
  const attrs = useMemo(() => Object.keys(sensitiveAttributes), [sensitiveAttributes]);
  if (!attrs.length) return null;

  return (
    <div className="card overflow-x-auto">
      <div className="text-sm font-medium mb-3">Bias heat-map</div>
      <table className="w-full text-xs font-mono border-separate border-spacing-1">
        <thead>
          <tr>
            <th className="text-left text-muted font-normal px-2 py-1">attribute \ metric</th>
            {METRIC_ORDER.map((m) => (
              <th
                key={m}
                className="text-left text-muted font-normal px-2 py-1 whitespace-nowrap"
                title={m}
              >
                {abbreviate(m)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {attrs.map((a) => {
            const metrics = sensitiveAttributes[a].metrics as Record<string, MetricResult>;
            return (
              <tr key={a}>
                <td className="px-2 py-1 text-fg whitespace-nowrap">{a}</td>
                {METRIC_ORDER.map((m) => {
                  const cell = metrics[m];
                  if (!cell) {
                    return (
                      <td key={m} className="px-2 py-1 text-center text-muted">
                        —
                      </td>
                    );
                  }
                  return (
                    <td
                      key={m}
                      className={`px-2 py-1 text-center rounded ${cellClass(cell.severity)}`}
                      title={cell.interpretation}
                    >
                      {cell.value.toFixed(3)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="flex items-center gap-3 mt-3 text-xs text-muted">
        <Legend label="pass" cls="bg-success/20 text-success" />
        <Legend label="warning" cls="bg-warning/20 text-warning" />
        <Legend label="fail" cls="bg-danger/20 text-danger" />
      </div>
    </div>
  );
}

function cellClass(severity: string): string {
  switch (severity) {
    case "pass":
      return "bg-success/15 text-success";
    case "warning":
      return "bg-warning/15 text-warning";
    case "fail":
      return "bg-danger/15 text-danger";
    default:
      return "bg-muted/10 text-muted";
  }
}

function Legend({ label, cls }: { label: string; cls: string }) {
  return <span className={`px-2 py-0.5 rounded ${cls}`}>{label}</span>;
}

function abbreviate(metric: string): string {
  const map: Record<string, string> = {
    demographic_parity_difference: "DP",
    disparate_impact_ratio: "DIR",
    equal_opportunity_difference: "EO",
    equalized_odds_difference: "EOdds",
    predictive_parity_difference: "PP",
    calibration_difference: "Cal",
  };
  return map[metric] ?? metric;
}
