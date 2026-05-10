"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  api,
  type HealthResponse,
  type PerformanceMetrics,
  type TransactionRecord,
} from "@/lib/api";
import { PageHeader } from "./page-header";
import { StatCard } from "./stat-card";
import { DecisionChart } from "./decision-chart";
import { TxnTable } from "./txn-table";
import { AlertFeed } from "./alert-feed";
import { PredictSandbox } from "./predict-sandbox";

function formatUptime(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function DashboardClient() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | undefined>();
  const [metricsNeedKey, setMetricsNeedKey] = useState(false);
  const [txns, setTxns] = useState<TransactionRecord[]>([]);
  const [metaErr, setMetaErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setMetaErr(null);
    try {
      setMetricsNeedKey(false);
      const [h, m, t] = await Promise.all([
        api.health(),
        api.metrics().catch((e) => {
          if (e instanceof ApiError && e.status === 401) {
            setMetricsNeedKey(true);
            return undefined;
          }
          throw e;
        }),
        api.transactions(30).catch((e) => {
          if (e instanceof ApiError && e.status === 401) {
            return [] as TransactionRecord[];
          }
          throw e;
        }),
      ]);
      setHealth(h);
      setMetrics(m);
      setTxns(Array.isArray(t) ? t : []);
    } catch (e) {
      if (e instanceof ApiError) {
        setMetaErr(`${e.status}: ${e.body?.slice(0, 300) || e.message}`);
      } else {
        setMetaErr(e instanceof Error ? e.message : "Failed to load");
      }
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 15_000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div>
      <PageHeader
        title="Operations console"
        description="Rolling KPIs, recent scored transactions, and a live WebSocket alert stream wired to the FastAPI plane."
      />

      {metaErr ? (
        <div className="mb-6 rounded-lg border border-risk-review/30 bg-risk-review/10 px-4 py-3 text-sm text-risk-review">
          {metaErr}
          <span className="mt-2 block text-xs text-ink-muted">
            Ensure the API is running and set NEXT_PUBLIC_API_BASE. If AUTH_MODE=api_key,
            set NEXT_PUBLIC_API_KEY to match API_KEYS.
          </span>
        </div>
      ) : null}

      {health ? (
        <div className="mb-2 flex flex-wrap items-center gap-3 text-xs text-ink-muted">
          <span
            className={
              health.db_connected && health.model_loaded
                ? "text-risk-ok"
                : "text-risk-review"
            }
          >
            ● {health.status}
          </span>
          <span>DB {health.db_connected ? "up" : "down"}</span>
          <span>Model {health.model_loaded ? "loaded" : "missing"}</span>
          <span className="font-mono">v{health.model_version}</span>
          <span>Uptime {formatUptime(health.uptime_seconds)}</span>
        </div>
      ) : null}

      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total predictions (window)"
          value={metrics ? String(metrics.total_predictions) : "—"}
          hint={
            metrics
              ? `Window ${metrics.window_size} · ${new Date(metrics.computed_at).toLocaleTimeString()}`
              : metricsNeedKey && !metaErr
                ? "401: set NEXT_PUBLIC_API_KEY when API auth is enabled"
                : undefined
          }
        />
        <StatCard
          label="Avg fraud probability"
          value={
            metrics
              ? `${(metrics.avg_fraud_probability * 100).toFixed(2)}%`
              : "—"
          }
        />
        <StatCard
          label="Avg latency"
          value={
            metrics ? `${metrics.avg_processing_time_ms.toFixed(1)} ms` : "—"
          }
        />
        <StatCard
          label="Fraud rate (estimate)"
          value={
            metrics
              ? `${(metrics.fraud_rate_estimate * 100).toFixed(2)}%`
              : "—"
          }
        />
      </div>

      <div className="mb-8 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-medium text-white">Decision mix</h2>
          <DecisionChart
            blocked={metrics?.blocked_count ?? 0}
            review={metrics?.review_count ?? 0}
            approved={metrics?.approved_count ?? 0}
          />
        </div>
        <div>
          <h2 className="mb-3 text-sm font-medium text-white">Alerts</h2>
          <AlertFeed />
        </div>
      </div>

      <div className="mb-8">
        <PredictSandbox onScored={() => void refresh()} />
      </div>

      <div className="rounded-xl border border-white/8 bg-canvas-elevated/60 shadow-panel">
        <div className="border-b border-white/8 px-5 py-4">
          <h2 className="text-sm font-medium text-white">Recent transactions</h2>
          <p className="text-xs text-ink-muted">GET /api/v1/transactions?limit=30</p>
        </div>
        <div className="p-4">
          <TxnTable rows={txns} />
        </div>
      </div>
    </div>
  );
}
