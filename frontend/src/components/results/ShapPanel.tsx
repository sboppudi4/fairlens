import { AlertTriangle } from "lucide-react";
import type { AuditResults } from "@/types";

export default function ShapPanel({ shap }: { shap?: AuditResults["shap"] }) {
  if (!shap) return null;

  if (!shap.available) {
    return (
      <section>
        <h2 className="text-lg font-semibold mb-3">SHAP explainability</h2>
        <div className="card text-sm text-muted">
          SHAP analysis was not produced for this audit. {shap.reason}
        </div>
      </section>
    );
  }

  const top = (shap.feature_importance ?? []).slice(0, 12);
  const max = Math.max(...top.map((f) => f.mean_abs_shap), 1e-9);

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">SHAP explainability</h2>
      <div className="card">
        <div className="text-xs text-muted mb-2">
          Explained {shap.n_samples_explained?.toLocaleString()} samples · {shap.n_features} engineered features
        </div>
        <h3 className="font-medium text-sm mb-3">Global feature importance</h3>
        <div className="space-y-1.5">
          {top.map((f) => (
            <div key={f.feature} className="flex items-center gap-3 text-xs">
              <div className="w-44 truncate font-mono" title={f.feature}>
                {f.feature}
              </div>
              <div className="flex-1 h-3 bg-bg rounded">
                <div
                  className="h-3 bg-accent rounded"
                  style={{ width: `${(f.mean_abs_shap / max) * 100}%` }}
                />
              </div>
              <div className="w-20 text-right font-mono">{f.mean_abs_shap.toFixed(4)}</div>
            </div>
          ))}
        </div>
      </div>

      {shap.proxy_warnings && shap.proxy_warnings.length > 0 && (
        <div className="card border-warning/40">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-warning">Proxy discrimination warnings</h3>
              <p className="text-xs text-muted mt-1">
                Features whose SHAP importance varies materially across demographic groups — a signal
                they may be encoding the sensitive attribute through correlation.
              </p>
            </div>
          </div>
          <ul className="mt-4 space-y-2 text-sm">
            {shap.proxy_warnings.slice(0, 8).map((w, i) => (
              <li key={i} className="border-l-2 pl-3 border-warning/40">
                <div className="text-xs text-muted">
                  attr <span className="font-mono">{w.sensitive_attribute}</span> · feature{" "}
                  <span className="font-mono">{w.feature}</span> · rel gap{" "}
                  <span className="font-mono">{(w.relative_gap * 100).toFixed(1)}%</span>
                </div>
                <div className="text-xs">{w.interpretation}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
