import { FormEvent, ReactNode, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Upload as UploadIcon } from "lucide-react";
import { listDatasets, uploadDataset, getDataset } from "@/api/datasets";
import { createAudit } from "@/api/audits";
import { extractErrorMessage } from "@/api/client";

export default function NewAudit() {
  const navigate = useNavigate();
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });

  const [step, setStep] = useState<1 | 2>(1);
  const [datasetId, setDatasetId] = useState<string>("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Step 2 fields
  const [name, setName] = useState("New audit");
  const [description, setDescription] = useState("");
  const [labelColumn, setLabelColumn] = useState("");
  const [predictionColumn, setPredictionColumn] = useState("");
  const [sensitive, setSensitive] = useState<string[]>([]);
  const [positiveLabel, setPositiveLabel] = useState("");
  const [favorablePrediction, setFavorablePrediction] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const selected = useQuery({
    queryKey: ["dataset", datasetId],
    queryFn: () => getDataset(datasetId),
    enabled: !!datasetId,
  });

  const columns = useMemo(() => selected.data?.column_names ?? [], [selected.data]);

  const uploadMut = useMutation({
    mutationFn: (file: File) => uploadDataset(file),
    onSuccess: (ds) => {
      setDatasetId(ds.id);
      setUploadError(null);
      setStep(2);
    },
    onError: (err) => setUploadError(extractErrorMessage(err, "Upload failed")),
  });

  const createMut = useMutation({
    mutationFn: createAudit,
    onSuccess: (a) => navigate(`/audits/${a.id}`),
    onError: (err) => setSubmitError(extractErrorMessage(err, "Failed to create audit")),
  });

  function onFileSelected(file: File) {
    setUploadError(null);
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setUploadError("Please upload a .csv file");
      return;
    }
    uploadMut.mutate(file);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    if (!datasetId) {
      setSubmitError("Select or upload a dataset first");
      return;
    }
    if (sensitive.length === 0) {
      setSubmitError("Pick at least one sensitive attribute");
      return;
    }
    createMut.mutate({
      dataset_id: datasetId,
      name,
      description: description || undefined,
      config: {
        label_column: labelColumn,
        prediction_column: predictionColumn,
        sensitive_attributes: sensitive,
        positive_label: positiveLabel,
        favorable_prediction: favorablePrediction,
        model_type: "binary_classification",
      },
    });
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">New audit</h1>
        <p className="text-muted text-sm">Step {step} of 2</p>
      </div>

      {step === 1 && (
        <div className="card space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-1">1. Choose a dataset</h2>
            <p className="text-sm text-muted">
              Upload a CSV with model predictions, or select one of your existing datasets.
            </p>
          </div>

          <label className="block">
            <div
              className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-accent transition-colors"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const f = e.dataTransfer.files?.[0];
                if (f) onFileSelected(f);
              }}
            >
              <UploadIcon className="w-8 h-8 mx-auto text-muted mb-2" />
              <div className="text-sm">
                <span className="text-accent font-medium">Click to browse</span> or drag a .csv here
              </div>
              <div className="text-xs text-muted mt-1">UTF-8, header row, ≥ 100 rows, ≤ 50 MB</div>
            </div>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onFileSelected(f);
              }}
            />
          </label>
          {uploadMut.isPending && <p className="text-sm text-muted">Uploading…</p>}
          {uploadError && <p className="text-sm text-danger">{uploadError}</p>}

          {datasets.data && datasets.data.length > 0 && (
            <div>
              <div className="text-sm text-muted mb-2">…or pick an existing dataset:</div>
              <div className="grid gap-2">
                {datasets.data.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      setDatasetId(d.id);
                      setStep(2);
                    }}
                    className="text-left p-3 rounded border border-border hover:border-accent transition-colors"
                  >
                    <div className="font-medium">{d.name}</div>
                    <div className="text-xs text-muted">
                      {d.row_count.toLocaleString()} rows · {d.column_names.length} cols ·{" "}
                      {new Date(d.created_at).toLocaleDateString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {step === 2 && (
        <form onSubmit={onSubmit} className="card space-y-5">
          <div>
            <h2 className="text-lg font-semibold mb-1">2. Configure the audit</h2>
            {selected.data && (
              <p className="text-sm text-muted">
                Dataset: <span className="font-mono">{selected.data.name}</span> ·{" "}
                {selected.data.row_count.toLocaleString()} rows
              </p>
            )}
          </div>

          <Field label="Audit name" required>
            <input value={name} onChange={(e) => setName(e.target.value)} className="input" required />
          </Field>
          <Field label="Description (optional)">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input"
              rows={2}
            />
          </Field>

          <Field label="Label column (ground truth)" required>
            <ColumnSelect value={labelColumn} onChange={setLabelColumn} columns={columns} />
          </Field>
          <Field label="Prediction column (model output)" required>
            <ColumnSelect value={predictionColumn} onChange={setPredictionColumn} columns={columns} exclude={[labelColumn]} />
          </Field>

          <Field label="Sensitive attributes (1–5)" required>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {columns
                .filter((c) => c !== labelColumn && c !== predictionColumn)
                .map((c) => {
                  const checked = sensitive.includes(c);
                  return (
                    <label key={c} className={`flex items-center gap-2 px-3 py-2 rounded border ${checked ? "border-accent bg-accent/10" : "border-border"}`}>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            if (sensitive.length >= 5) return;
                            setSensitive([...sensitive, c]);
                          } else {
                            setSensitive(sensitive.filter((s) => s !== c));
                          }
                        }}
                      />
                      <span className="text-sm">{c}</span>
                    </label>
                  );
                })}
            </div>
          </Field>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Positive label value" required>
              <input
                value={positiveLabel}
                onChange={(e) => setPositiveLabel(e.target.value)}
                className="input"
                placeholder='e.g. ">50K" or "1"'
                required
              />
            </Field>
            <Field label="Favorable prediction value" required>
              <input
                value={favorablePrediction}
                onChange={(e) => setFavorablePrediction(e.target.value)}
                className="input"
                placeholder='e.g. ">50K" or "1"'
                required
              />
            </Field>
          </div>

          {submitError && <p className="text-sm text-danger">{submitError}</p>}

          <div className="flex justify-between pt-2">
            <button type="button" onClick={() => setStep(1)} className="btn-ghost">
              ← Back
            </button>
            <button type="submit" disabled={createMut.isPending} className="btn-primary">
              {createMut.isPending ? "Launching…" : "Launch audit"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">
        {label} {required && <span className="text-danger">*</span>}
      </label>
      {children}
    </div>
  );
}

function ColumnSelect({
  value,
  onChange,
  columns,
  exclude = [],
}: {
  value: string;
  onChange: (s: string) => void;
  columns: string[];
  exclude?: string[];
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="input" required>
      <option value="">— select —</option>
      {columns
        .filter((c) => !exclude.includes(c))
        .map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
    </select>
  );
}
