"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  api,
  type HealthResponse,
  type PerformanceMetrics,
  type TransactionRecord,
} from "@/lib/api";
import { DashboardHero } from "./dashboard-hero";
import { StatCard } from "./stat-card";
import { DecisionChart } from "./decision-chart";
import { TxnTable } from "./txn-table";
import { AlertFeed } from "./alert-feed";
import { PredictSandbox } from "./predict-sandbox";
import { Panel, PanelHeader } from "./panel";
import { BarChart3, Percent, Timer, TrendingUp } from "lucide-react";

export function DashboardClient() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | undefined>();
  const [metricsNeedKey, setMetricsNeedKey] = useState(false);
  const [txns, setTxns] = useState<TransactionRecord[]>([]);
  const [metaErr, setMetaErr] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [initial, setInitial] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    setMetaErr(null);
    setRefreshing(true);
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
      setLastUpdated(new Date());
    } catch (e) {
      if (e instanceof ApiError) {
        setMetaErr(`${e.status}: ${e.body?.slice(0, 300) || e.message}`);
      } else {
        setMetaErr(e instanceof Error ? e.message : "Failed to load");
      }
    } finally {
      setRefreshing(false);
      setInitial(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 15_000);
    return () => clearInterval(id);
  }, [refresh]);

  const showSkeleton = initial && !health && !metaErr;

  return (
    <div className="pb-16">
      <DashboardHero
        health={health}
        onRefresh={() => void refresh()}
        refreshing={refreshing}
        lastUpdated={lastUpdated}
      />

      {metaErr ? (
        <div className="mb-8 rounded-2xl border border-amber-500/25 bg-amber-500/[0.08] px-5 py-4 text-sm text-amber-100">
          <p className="font-medium text-amber-50">Could not reach the API</p>
          <p className="mt-1 font-mono text-xs opacity-90">{metaErr}</p>
          <p className="mt-3 text-xs leading-relaxed text-amber-200/80">
            Run the FastAPI stack (e.g.{" "}
            <span className="font-mono text-white/90">docker compose up</span>), then
            set{" "}
            <span className="font-mono text-white/90">NEXT_PUBLIC_API_BASE</span>. If{" "}
            <span className="font-mono text-white/90">AUTH_MODE=api_key</span>, add{" "}
            <span className="font-mono text-white/90">NEXT_PUBLIC_API_KEY</span> to{" "}
            <span className="font-mono text-white/90">.env.local</span>.
          </p>
        </div>
      ) : null}

      {metricsNeedKey && !metaErr ? (
        <div className="mb-8 flex flex-wrap items-center gap-3 rounded-2xl border border-cyan-500/20 bg-cyan-500/[0.06] px-5 py-4 text-sm text-cyan-100">
          <span className="rounded-md bg-cyan-400/20 px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-cyan-200">
            Tip
          </span>
          <span>
            Authenticated metrics returned 401 — add{" "}
            <span className="font-mono text-white">NEXT_PUBLIC_API_KEY</span> so KPI
            cards and the transaction list populate for your Upwork demo recording.
          </span>
        </div>
      ) : null}

      <div className="mb-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Predictions (window)"
          value={metrics ? metrics.total_predictions.toLocaleString() : "—"}
          hint={
            metrics
              ? `Rolling ${metrics.window_size.toLocaleString()} · ${new Date(metrics.computed_at).toLocaleTimeString()}`
              : metricsNeedKey && !metaErr
                ? "Requires API key when auth is enabled"
                : undefined
          }
          icon={BarChart3}
          skeleton={showSkeleton}
        />
        <StatCard
          label="Avg fraud probability"
          value={
            metrics
              ? `${(metrics.avg_fraud_probability * 100).toFixed(2)}%`
              : "—"
          }
          icon={Percent}
          skeleton={showSkeleton}
        />
        <StatCard
          label="Avg latency"
          value={
            metrics ? `${metrics.avg_processing_time_ms.toFixed(1)} ms` : "—"
          }
          icon={Timer}
          skeleton={showSkeleton}
        />
        <StatCard
          label="Fraud rate (est.)"
          value={
            metrics
              ? `${(metrics.fraud_rate_estimate * 100).toFixed(2)}%`
              : "—"
          }
          icon={TrendingUp}
          skeleton={showSkeleton}
        />
      </div>

      <div className="mb-10 grid gap-6 lg:grid-cols-5">
        <Panel className="lg:col-span-3">
          <PanelHeader
            title="Decision distribution"
            subtitle="Share of APPROVED / REVIEW / BLOCKED outcomes inside the performance tracker window — updates on the same cadence as your API metrics."
          />
          <DecisionChart
            blocked={metrics?.blocked_count ?? 0}
            review={metrics?.review_count ?? 0}
            approved={metrics?.approved_count ?? 0}
          />
        </Panel>
        <div className="flex min-h-0 lg:col-span-2">
          <AlertFeed />
        </div>
      </div>

      <div className="mb-10">
        <PredictSandbox onScored={() => void refresh()} />
      </div>

      <Panel>
        <PanelHeader
          title="Audit trail"
          subtitle="Recent persisted scores — ideal proof for clients that this is a full stack, not a static mock."
        />
        <TxnTable rows={txns} />
      </Panel>

      <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 border-t border-white/[0.06] pt-10 font-mono text-[10px] uppercase tracking-[0.25em] text-ink-faint">
        <span>FastAPI</span>
        <span className="text-white/20">·</span>
        <span>Postgres</span>
        <span className="text-white/20">·</span>
        <span>WebSockets</span>
        <span className="text-white/20">·</span>
        <span>SHAP</span>
        <span className="text-white/20">·</span>
        <span>XGBoost</span>
        <span className="text-white/20">·</span>
        <span>Next.js 14</span>
      </div>
    </div>
  );
}
