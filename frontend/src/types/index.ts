export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
  user: User;
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  filename: string;
  row_count: number;
  column_names: string[];
  column_types: Record<string, string>;
  file_size_bytes: number;
  status: string;
  created_at: string;
}

export interface AuditConfig {
  label_column: string;
  prediction_column: string;
  sensitive_attributes: string[];
  positive_label: string;
  favorable_prediction: string;
  model_type: string;
}

export interface Audit {
  id: string;
  dataset_id: string;
  name: string;
  description: string | null;
  config: AuditConfig;
  status: "pending" | "running" | "completed" | "failed";
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  results?: AuditResults | null;
}

export interface AuditStatus {
  id: string;
  status: string;
  progress: number;
  stage: string | null;
  error_message: string | null;
}

export interface MetricResult {
  name: string;
  value: number;
  threshold: number;
  passes: boolean;
  severity: "pass" | "warning" | "fail";
  interpretation: string;
  direction: string;
  per_group: Record<string, unknown>;
  pairwise?: Array<{ group_a: string; group_b: string; gap: number }>;
}

export interface AuditResults {
  schema_version: string;
  summary: {
    overall_fairness_score: number;
    risk_level: "Low Risk" | "Medium Risk" | "High Risk";
    metrics_passing: number;
    metrics_total: number;
    severities: { pass: number; warning: number; fail: number };
  };
  sensitive_attributes: Record<
    string,
    {
      metrics: Record<string, MetricResult>;
      per_group_performance: Record<string, Record<string, unknown>>;
    }
  >;
  regulatory: {
    frameworks: Array<{
      framework: string;
      compliant: number;
      non_compliant: number;
      total: number;
      compliance_percentage: number;
      status: "compliant" | "partial" | "non_compliant";
    }>;
    cross_cutting: Array<{
      framework: string;
      locator: string;
      title: string;
      quote: string;
      rationale: string;
    }>;
    per_metric: Array<{
      sensitive_attribute: string;
      metric: string;
      framework: string;
      locator: string;
      title: string;
      quote: string;
      rationale: string;
      status: "compliant" | "non_compliant";
      action_required: string | null;
    }>;
  };
  config_used: AuditConfig;
  dataset: { id: string; row_count: number };
  completed_at: string;
  shap?: {
    available: boolean;
    reason?: string;
    n_samples_explained?: number;
    n_features?: number;
    feature_importance?: Array<{ feature: string; mean_abs_shap: number }>;
    per_group?: Record<string, Record<string, Array<{ feature: string; mean_abs_shap: number }>>>;
    proxy_warnings?: Array<{
      sensitive_attribute: string;
      feature: string;
      max_group_importance: number;
      min_group_importance: number;
      relative_gap: number;
      interpretation: string;
    }>;
  };
  mitigations?: Array<{
    sensitive_attribute: string;
    failing_metric: string;
    metric_value: number | null;
    metric_severity: string;
    technique: string;
    description: string;
    complexity: "low" | "medium" | "high";
    expected_improvement: string;
    code_snippet: string;
    reference: string;
    flagged_features?: string[];
  }>;
}

export interface ColumnInfo {
  name: string;
  type: string;
  cardinality: number;
  null_count: number;
  sample_values: unknown[];
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface ReportStatus {
  audit_id: string;
  ready: boolean;
  report: { id: string; audit_id: string; file_size_bytes: number; download_count: number; generated_at: string } | null;
  progress: number;
  stage: string | null;
}
