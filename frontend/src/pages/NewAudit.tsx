import { FormEvent, ReactNode, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Database } from "lucide-react";
import { listDatasets, uploadDataset, getDataset, getDatasetPreview } from "@/api/datasets";
import { createAudit } from "@/api/audits";
import { extractErrorMessage } from "@/api/client";
import FileDropzone from "@/components/upload/FileDropzone";
import ColumnMapper from "@/components/upload/ColumnMapper";
import DataPreview from "@/components/upload/DataPreview";
import { formatRelativeTime } from "@/utils/formatters";

export default function NewAudit() {
  const navigate = useNavigate();
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [datasetId, setDatasetId] = useState<string>("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [name, setName] = useState("New audit");
  const [description, setDescription] = useState("");
  const [labelColumn, setLabelColumn] = useState("");
  const [predictionColumn, setPredictionColumn] = useState("");
  const [sensitive, setSensitive] = useState<string[]>([]);
  const [positiveLabel, setPositiveLabel] = useState("");
  const [favorablePrediction, setFavorablePrediction] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    label?: string;
    prediction?: string;
    sensitive?: string;
  }>({});

  const selected = useQuery({
    queryKey: ["dataset", datasetId],
    queryFn: () => getDataset(datasetId),
    enabled: !!datasetId,
  });

  const preview = useQuery({
    queryKey: ["dataset-preview", datasetId],
    queryFn: () => getDatasetPreview(datasetId, 20),
    enabled: !!datasetId,
  });

  const columns = useMemo(() => selected.data?.column_names ?? [], [selected.data]);
  const columnTypes = useMemo(() => selected.data?.column_types ?? {}, [selected.data]);

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

  function validateStep2(): boolean {
    const errs: typeof fieldErrors = {};
    if (!labelColumn) errs.label = "Pick the ground-truth label column";
    if (!predictionColumn) errs.prediction = "Pick the prediction column";
    if (sensitive.length === 0) errs.sensitive = "Select at least one sensitive attribute";
    if (sensitive.length > 5) errs.sensitive = "At most 5 sensitive attributes";
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    if (!validateStep2()) return;
    if (!positiveLabel || !favorablePrediction) {
      setSubmitError("Specify the positive label and favorable prediction values");
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

  function toggleSensitive(col: string) {
    setSensitive((cur) => {
      if (cur.includes(col)) return cur.filter((s) => s !== col);
      if (cur.length >= 5) return cur;
      return [...cur, col];
    });
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">New audit</h1>
          <p className="text-muted text-sm">Step {step} of 3</p>
        </div>
        <StepIndicator step={step} />
      </header>

      {step === 1 && (
        <div className="card space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-1">1. Choose a dataset</h2>
            <p className="text-sm text-muted">
              Upload a CSV with model predictions, or select one of your existing datasets.
            </p>
          </div>

          <FileDropzone
            onAccept={(f) => uploadMut.mutate(f)}
            isUploading={uploadMut.isPending}
            errorMessage={uploadError}
          />

          {datasets.data && datasets.data.length > 0 && (
            <div>
              <div className="text-sm text-muted mb-2 flex items-center gap-2">
                <Database className="w-4 h-4" />
                …or pick an existing dataset
              </div>
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
                      {formatRelativeTime(d.created_at)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          {preview.data && (
            <DataPreview
              columns={preview.data.columns}
              rows={preview.data.rows}
              rowCount={preview.data.row_count}
            />
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (validateStep2()) setStep(3);
            }}
            className="card space-y-5"
          >
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

            <ColumnMapper
              columns={columns}
              columnTypes={columnTypes}
              labelColumn={labelColumn}
              predictionColumn={predictionColumn}
              sensitiveAttributes={sensitive}
              onLabelChange={setLabelColumn}
              onPredictionChange={setPredictionColumn}
              onSensitiveToggle={toggleSensitive}
              errors={fieldErrors}
            />

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

            <div className="flex justify-between pt-2">
              <button type="button" onClick={() => setStep(1)} className="btn-ghost">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button type="submit" className="btn-primary">
                Review <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      )}

      {step === 3 && (
        <form onSubmit={onSubmit} className="card space-y-5">
          <h2 className="text-lg font-semibold">3. Review and launch</h2>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <Summary label="Audit" value={name} />
            <Summary label="Dataset" value={selected.data?.name ?? "—"} />
            <Summary label="Label column" value={labelColumn} />
            <Summary label="Prediction column" value={predictionColumn} />
            <Summary label="Sensitive attributes" value={sensitive.join(", ")} />
            <Summary label="Positive label" value={positiveLabel} />
            <Summary label="Favorable prediction" value={favorablePrediction} />
            <Summary label="Estimated runtime" value={estimateRuntime(selected.data?.row_count ?? 0)} />
          </dl>
          {submitError && (
            <p className="text-sm text-danger" role="alert">
              {submitError}
            </p>
          )}
          <div className="flex justify-between pt-2">
            <button type="button" onClick={() => setStep(2)} className="btn-ghost">
              <ArrowLeft className="w-4 h-4" /> Back
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

function Field({ label, required, children }: { label: string; required?: boolean; children: ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">
        {label} {required && <span className="text-danger">*</span>}
      </label>
      {children}
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted uppercase tracking-wider">{label}</dt>
      <dd className="font-mono text-sm mt-0.5">{value || "—"}</dd>
    </div>
  );
}

function StepIndicator({ step }: { step: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center gap-1.5">
      {[1, 2, 3].map((n) => (
        <div
          key={n}
          className={`h-1.5 w-8 rounded ${n <= step ? "bg-accent" : "bg-border"}`}
          aria-current={n === step ? "step" : undefined}
        />
      ))}
    </div>
  );
}

function estimateRuntime(rowCount: number): string {
  if (rowCount < 1_000) return "< 30s";
  if (rowCount < 10_000) return "~1 min";
  if (rowCount < 100_000) return "~3 min";
  return "5–10 min";
}
