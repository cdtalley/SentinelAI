"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import {
  ApiError,
  api,
  type DriftReport,
  type HealthResponse,
} from "@/lib/api";
import { StatCard } from "./stat-card";
import { Panel, PanelHeader } from "./panel";
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
        .map(([name, psi]) => ({
          name: name.length > 14 ? `${name.slice(0, 12)}…` : name,
          psi,
        }))
        .sort((a, b) => b.psi - a.psi)
        .slice(0, 12)
    : [];

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-canvas-elevated/70 p-6 sm:p-8">
        <div className="pointer-events-none absolute -left-20 bottom-0 h-48 w-48 rounded-full bg-violet-500/10 blur-3xl" />
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">
          Governance &amp; reliability
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Model health &amp; drift
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-muted">
          Readiness-style signals plus PSI from{" "}
          <span className="font-mono text-accent/90">GET /api/v1/transactions/drift</span>{" "}
          — the narrative hiring managers expect next to a fraud model pitch.
        </p>
      </div>

      <Panel>
        <PanelHeader
          title="Controls"
          subtitle="Refresh pulls latest health + drift; baseline captures PSI reference from SHAP history."
          action={
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void load()}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-ink transition hover:border-accent/30 hover:text-white disabled:opacity-50"
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
                className="inline-flex items-center gap-2 rounded-xl bg-white/[0.08] px-4 py-2 text-sm font-medium text-white transition hover:bg-white/[0.12] disabled:opacity-50"
              >
                {baselineBusy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Establish baseline
              </button>
            </div>
          }
        />
        {err ? (
          <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {err}
          </div>
        ) : null}
        {baselineMsg ? (
          <div className="mt-4 rounded-xl border border-white/10 bg-canvas/50 px-4 py-3 font-mono text-xs text-ink-muted">
            {baselineMsg}
          </div>
        ) : null}
      </Panel>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading && !health ? (
          <>
            <StatCard label="API status" value="—" skeleton />
            <StatCard label="Model" value="—" skeleton />
            <StatCard label="Database" value="—" skeleton />
            <StatCard label="Ollama" value="—" skeleton />
          </>
        ) : health ? (
          <>
            <StatCard
              label="API status"
              value={health.status}
              hint={`Served ${health.total_predictions_served.toLocaleString()}`}
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
              label="Ollama"
              value={health.ollama_available ? "UP" : "OFF"}
              hint="Narrative explanations"
            />
          </>
        ) : null}
      </div>

      {drift ? (
        <div className="space-y-6">
          <Panel>
            <PanelHeader
              title="Drift summary"
              subtitle={`Window ${drift.window_size.toLocaleString()} · checked ${new Date(drift.checked_at).toLocaleString()}`}
            />
            <div className="flex flex-wrap gap-8">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-wider text-ink-faint">
                  Drift detected
                </p>
                <p
                  className={
                    drift.drift_detected
                      ? "mt-1 text-2xl font-semibold text-rose-300"
                      : "mt-1 text-2xl font-semibold text-emerald-300"
                  }
                >
                  {drift.drift_detected ? "Yes" : "No"}
                </p>
              </div>
              {drift.features_with_drift.length > 0 ? (
                <div className="min-w-[200px] flex-1">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-ink-faint">
                    Features flagged
                  </p>
                  <p className="mt-1 text-sm text-amber-100">
                    {drift.features_with_drift.join(", ")}
                  </p>
                </div>
              ) : null}
            </div>
          </Panel>

          <Panel>
            <PanelHeader
              title="PSI by feature"
              subtitle="Population stability — strongest slide in an MLOps client review."
            />
            <div className="h-[340px] w-full rounded-xl border border-white/[0.06] bg-canvas/40 p-2">
              {psiData.length === 0 ? (
                <p className="flex h-full items-center justify-center px-6 text-center text-sm text-ink-muted">
                  No PSI scores yet — run predictions so SHAP-backed history exists, then
                  refresh or establish baseline.
                </p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={psiData} margin={{ bottom: 52, left: 8, right: 8 }}>
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#64748b", fontSize: 10 }}
                      angle={-35}
                      textAnchor="end"
                      height={64}
                    />
                    <YAxis
                      tick={{ fill: "#64748b", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#0c101c",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: "10px",
                        fontSize: "12px",
                      }}
                    />
                    <Bar
                      dataKey="psi"
                      fill="#22d3ee"
                      radius={[6, 6, 0, 0]}
                      maxBarSize={44}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>
        </div>
      ) : null}
    </div>
  );
}
