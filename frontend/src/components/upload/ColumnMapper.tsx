import { Check } from "lucide-react";

export interface ColumnMapperProps {
  columns: string[];
  columnTypes?: Record<string, string>;
  labelColumn: string;
  predictionColumn: string;
  sensitiveAttributes: string[];
  onLabelChange: (col: string) => void;
  onPredictionChange: (col: string) => void;
  onSensitiveToggle: (col: string) => void;
  errors?: Partial<Record<"label" | "prediction" | "sensitive", string>>;
}

const TYPE_BADGE: Record<string, string> = {
  numeric: "bg-accent/10 text-accent",
  boolean: "bg-success/10 text-success",
  categorical: "bg-warning/10 text-warning",
  string: "bg-muted/20 text-muted",
};

export default function ColumnMapper({
  columns,
  columnTypes = {},
  labelColumn,
  predictionColumn,
  sensitiveAttributes,
  onLabelChange,
  onPredictionChange,
  onSensitiveToggle,
  errors = {},
}: ColumnMapperProps) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field
          label="Ground-truth label column"
          help="The column with the actual outcome (what really happened)."
          error={errors.label}
        >
          <select className="input" value={labelColumn} onChange={(e) => onLabelChange(e.target.value)}>
            <option value="">— select —</option>
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>

        <Field
          label="Model prediction column"
          help="The column with the model's predicted outcome."
          error={errors.prediction}
        >
          <select
            className="input"
            value={predictionColumn}
            onChange={(e) => onPredictionChange(e.target.value)}
          >
            <option value="">— select —</option>
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">
          Sensitive attributes <span className="text-muted">(1–5)</span>
        </label>
        <p className="text-xs text-muted mb-2">
          Demographic columns to evaluate for bias (e.g. gender, race, age group).
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {columns
            .filter((c) => c !== labelColumn && c !== predictionColumn)
            .map((c) => {
              const checked = sensitiveAttributes.includes(c);
              const dtype = columnTypes[c] ?? "string";
              return (
                <button
                  type="button"
                  key={c}
                  onClick={() => onSensitiveToggle(c)}
                  aria-pressed={checked}
                  className={[
                    "flex items-center justify-between gap-2 px-3 py-2 rounded-md border text-sm text-left transition-colors",
                    checked
                      ? "border-accent bg-accent/10"
                      : "border-border hover:border-accent/40",
                  ].join(" ")}
                >
                  <span className="flex items-center gap-2 min-w-0">
                    <span
                      className={`text-[10px] uppercase tracking-wider rounded px-1.5 py-0.5 shrink-0 ${
                        TYPE_BADGE[dtype] ?? TYPE_BADGE.string
                      }`}
                    >
                      {dtype}
                    </span>
                    <span className="font-mono truncate">{c}</span>
                  </span>
                  {checked && <Check className="w-4 h-4 text-accent shrink-0" />}
                </button>
              );
            })}
        </div>
        {errors.sensitive && (
          <p className="text-sm text-danger mt-2" role="alert">
            {errors.sensitive}
          </p>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  help,
  error,
  children,
}: {
  label: string;
  help?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      {help && <p className="text-xs text-muted mb-2">{help}</p>}
      {children}
      {error && (
        <p className="text-sm text-danger mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
