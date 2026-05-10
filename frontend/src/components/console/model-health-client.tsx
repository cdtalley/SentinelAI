"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import {
  ApiError,
  api,
  type DriftReport,
  type HealthResponse,
} from "@/lib/api";
import { PageHeader } from "./page-header";
import { StatCard } from "./stat-card";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ModelHealthClient() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [drift, setDrift] = useState<DriftReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [baselineMsg, setBaselineMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [baselineBusy, setBaselineBusy] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const [h, d] = await Promise.all([api.health(), api.drift()]);
      setHealth(h);
      setDrift(d);
    } catch (e) {
      if (e instanceof ApiError) {
        setErr(`${e.status}: ${e.body?.slice(0, 400) || e.message}`);
      } else {
        setErr(e instanceof Error ? e.message : "Failed to load");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function baseline() {
    setBaselineMsg(null);
    setBaselineBusy(true);
    try {
      const r = await api.establishDriftBaseline();
      setBaselineMsg(r.message);
      await load();
    } catch (e) {
      if (e instanceof ApiError) {
        setBaselineMsg(`${e.status}: ${e.body?.slice(0, 300)}`);
      } else {
        setBaselineMsg(e instanceof Error ? e.message : "Failed");
      }
    } finally {
      setBaselineBusy(false);
    }
  }

  const psiData = drift
    ? Object.entries(drift.psi_scores)
        .map(([name, psi]) => ({ name: name.length > 14 ? `${name.slice(0, 12)}…` : name, psi }))
        .sort((a, b) => b.psi - a.psi)
        .slice(0, 12)
    : [];

  return (
    <div>
      <PageHeader
        title="Model health & drift"
        description="Health envelope plus PSI snapshot from GET /api/v1/transactions/drift — governance signal for production MLOps."
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-ink transition hover:border-accent/30 hover:text-white disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Refresh
        </button>
        <button
          type="button"
          onClick={() => void baseline()}
          disabled={baselineBusy}
          className="inline-flex items-center gap-2 rounded-lg bg-white/[0.06] px-4 py-2 text-sm text-white transition hover:bg-white/[0.1] disabled:opacity-50"
        >
          {baselineBusy ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : null}
          Establish drift baseline
        </button>
      </div>

      {err ? (
        <div className="mb-6 rounded-lg border border-risk-block/30 bg-risk-block/10 px-4 py-3 text-sm text-risk-block">
          {err}
        </div>
      ) : null}
      {baselineMsg ? (
        <div className="mb-6 rounded-lg border border-white/10 bg-canvas-elevated px-4 py-3 font-mono text-xs text-ink-muted">
          {baselineMsg}
        </div>
      ) : null}

      {health ? (
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="API status"
            value={health.status}
            hint={`Predictions served: ${health.total_predictions_served}`}
          />
          <StatCard
            label="Model"
            value={health.model_loaded ? "READY" : "NOT LOADED"}
            hint={health.model_version}
          />
          <StatCard
            label="Database"
            value={health.db_connected ? "CONNECTED" : "DOWN"}
          />
          <StatCard
            label="Ollama (narrative)"
            value={health.ollama_available ? "UP" : "OFF"}
          />
        </div>
      ) : null}

      {drift ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-4 rounded-xl border border-white/8 bg-canvas-elevated/60 px-5 py-4 shadow-panel">
            <div>
              <p className="font-mono text-xs text-ink-faint">Drift detected</p>
              <p
                className={
                  drift.drift_detected ? "text-xl text-risk-block" : "text-xl text-risk-ok"
                }
              >
                {drift.drift_detected ? "YES" : "NO"}
              </p>
            </div>
            <div>
              <p className="font-mono text-xs text-ink-faint">Window</p>
              <p className="text-xl text-white">{drift.window_size}</p>
            </div>
            <div>
              <p className="font-mono text-xs text-ink-faint">Checked</p>
              <p className="text-sm text-ink-muted">
                {new Date(drift.checked_at).toLocaleString()}
              </p>
            </div>
            {drift.features_with_drift.length > 0 ? (
              <div className="min-w-[200px] flex-1">
                <p className="font-mono text-xs text-ink-faint">Features flagged</p>
                <p className="text-sm text-risk-review">
                  {drift.features_with_drift.join(", ")}
                </p>
              </div>
            ) : null}
          </div>

          <div>
            <h2 className="mb-3 text-sm font-medium text-white">PSI by feature</h2>
            <div className="h-[320px] rounded-xl border border-white/8 bg-canvas-elevated/40 p-2">
              {psiData.length === 0 ? (
                <p className="flex h-full items-center justify-center text-sm text-ink-muted">
                  No PSI scores yet — ingest predictions with SHAP history first.
                </p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={psiData} margin={{ bottom: 48, left: 8, right: 8 }}>
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#64748b", fontSize: 10 }}
                      angle={-35}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis
                      tick={{ fill: "#64748b", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#0c101c",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="psi" fill="#22d3ee" radius={[4, 4, 0, 0]} maxBarSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
