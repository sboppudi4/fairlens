import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface Item {
  feature: string;
  mean_abs_shap: number;
}

interface Props {
  features: Item[];
  topK?: number;
  title?: string;
  height?: number;
}

const COLORS = ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"];

/** Horizontal bar chart of SHAP feature importance — the "waterfall" view. */
export default function ShapWaterfall({
  features,
  topK = 12,
  title = "Top features by mean |SHAP|",
  height = 360,
}: Props) {
  const data = useMemo(
    () =>
      [...features]
        .sort((a, b) => b.mean_abs_shap - a.mean_abs_shap)
        .slice(0, topK)
        .map((f) => ({ ...f, label: f.feature.length > 28 ? `${f.feature.slice(0, 26)}…` : f.feature })),
    [features, topK],
  );

  if (!data.length) {
    return (
      <div className="card text-sm text-muted">No feature importance data available.</div>
    );
  }

  return (
    <div className="card">
      <div className="text-sm font-medium mb-2">{title}</div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ left: 16, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.15)" horizontal={false} />
          <XAxis type="number" stroke="#64748b" fontSize={11} />
          <YAxis
            type="category"
            dataKey="label"
            stroke="#64748b"
            fontSize={11}
            width={170}
            interval={0}
          />
          <Tooltip
            contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 6 }}
            labelStyle={{ color: "#f1f5f9" }}
            formatter={(value: number) => value.toFixed(4)}
          />
          <Bar dataKey="mean_abs_shap" radius={[0, 4, 4, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
