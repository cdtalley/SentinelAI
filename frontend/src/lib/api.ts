import { getApiBase, getApiKey } from "./config";

export type HealthResponse = {
  status: string;
  model_loaded: boolean;
  model_version: string;
  ollama_available: boolean;
  db_connected: boolean;
  total_predictions_served: number;
  uptime_seconds: number;
};

export type PerformanceMetrics = {
  window_size: number;
  total_predictions: number;
  blocked_count: number;
  review_count: number;
  approved_count: number;
  fraud_rate_estimate: number;
  avg_fraud_probability: number;
  avg_processing_time_ms: number;
  model_version: string;
  computed_at: string;
};

export type TransactionRecord = {
  transaction_id: string;
  amount: number;
  fraud_probability: number;
  decision: string;
  model_used: string;
  is_cold_start: boolean;
  explanation: string;
  predicted_at: string;
};

export type DriftReport = {
  checked_at: string;
  window_size: number;
  features_with_drift: string[];
  psi_scores: Record<string, number>;
  drift_detected: boolean;
};

export type TransactionInput = {
  transaction_id?: string;
  time: number;
  amount: number;
  v1: number;
  v2: number;
  v3: number;
  v4: number;
  v5: number;
  v6: number;
  v7: number;
  v8: number;
  v9: number;
  v10: number;
  v11: number;
  v12: number;
  v13: number;
  v14: number;
  v15: number;
  v16: number;
  v17: number;
  v18: number;
  v19: number;
  v20: number;
  v21: number;
  v22: number;
  v23: number;
  v24: number;
  v25: number;
  v26: number;
  v27: number;
  v28: number;
};

export type SHAPFeature = {
  feature_name: string;
  shap_value: number;
  direction: "increases_risk" | "decreases_risk";
  abs_impact: number;
};

export type PredictionWithExplanation = {
  transaction_id: string;
  amount: number;
  fraud_probability: number;
  decision: "APPROVED" | "REVIEW" | "BLOCKED";
  model_used: "xgboost" | "isolation_forest";
  model_version: string;
  top_shap_features: SHAPFeature[];
  is_cold_start: boolean;
  processing_time_ms: number;
  predicted_at: string;
  explanation: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const headers = new Headers(init?.headers);
  if (
    init?.body &&
    typeof init.body === "string" &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }
  const key = getApiKey();
  if (key) {
    headers.set("X-API-Key", key);
  }
  const url = `${getApiBase()}${path}`;
  const res = await fetch(url, { ...init, headers, cache: "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.statusText || "Request failed", res.status, text);
  }
  if (res.status === 204) return {} as T;
  return res.json() as Promise<T>;
}

export function minimalTransactionInput(
  overrides: Partial<TransactionInput> = {}
): TransactionInput {
  const zeros = Object.fromEntries(
    Array.from({ length: 28 }, (_, i) => [`v${i + 1}`, 0])
  ) as Record<string, number>;
  return {
    time: 0,
    amount: 120.5,
    ...zeros,
    ...overrides,
  } as TransactionInput;
}

export const api = {
  health: () => fetchJson<HealthResponse>("/api/v1/health"),
  healthReady: () => fetch("/api/v1/health/ready", { cache: "no-store" }),
  metrics: () =>
    fetchJson<PerformanceMetrics>("/api/v1/metrics"),
  transactions: (limit = 50, decision?: string) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (decision) q.set("decision", decision);
    return fetchJson<TransactionRecord[]>(`/api/v1/transactions?${q}`);
  },
  transactionById: (transactionId: string) =>
    fetchJson<TransactionRecord>(
      `/api/v1/predict/${encodeURIComponent(transactionId)}`
    ),
  drift: () => fetchJson<DriftReport>("/api/v1/transactions/drift"),
  predict: (body: TransactionInput) =>
    fetchJson<PredictionWithExplanation>("/api/v1/predict", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  establishDriftBaseline: () =>
    fetchJson<{ message: string; feature_keys: string[] }>(
      "/api/v1/transactions/drift/baseline",
      { method: "POST" }
    ),
};
