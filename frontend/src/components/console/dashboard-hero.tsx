"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Cpu,
  Database,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { HealthResponse } from "@/lib/api";

export function DashboardHero({
  health,
  onRefresh,
  refreshing,
  lastUpdated,
}: {
  health: HealthResponse | null;
  onRefresh: () => void;
  refreshing: boolean;
  lastUpdated: Date | null;
}) {
  const [flash, setFlash] = useState(false);

  function handleRefresh() {
    setFlash(true);
    window.setTimeout(() => setFlash(false), 400);
    onRefresh();
  }

  const live =
    health && health.db_connected && health.model_loaded && health.status === "ok";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn(
        "relative mb-10 overflow-hidden rounded-2xl border border-white/[0.08] bg-canvas-elevated/80 p-6 sm:p-8",
        "shadow-[0_0_0_1px_rgba(34,211,238,0.06),0_32px_64px_-24px_rgba(0,0,0,0.55)]"
      )}
    >
      <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 left-1/3 h-48 w-96 rounded-full bg-violet-500/5 blur-3xl" />

      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 font-mono text-[10px] font-medium uppercase tracking-widest text-ink-muted">
              <Sparkles className="h-3 w-3 text-accent" />
              Live fraud console
            </span>
            {health ? (
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[10px] font-medium uppercase tracking-wider",
                  live
                    ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                    : "border-amber-500/25 bg-amber-500/10 text-amber-200"
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    live ? "animate-pulse bg-emerald-400" : "bg-amber-400"
                  )}
                />
                {live ? "Production path" : "Degraded / demo"}
              </span>
            ) : null}
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Decisions your{" "}
            <span className="bg-gradient-to-r from-accent via-cyan-200 to-emerald-300 bg-clip-text text-transparent">
              stakeholders trust
            </span>
            .
          </h1>
          <p className="mt-4 text-base leading-relaxed text-ink-muted sm:text-[17px]">
            One screen for KPIs, decision mix, live BLOCKED/REVIEW alerts, and a
            one-click scoring demo — wired to your real FastAPI + ML stack. Built
            to win enterprise and Upwork engagements on first impression.
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-stretch gap-3 sm:flex-row sm:items-center lg:flex-col lg:items-end">
          <button
            type="button"
            onClick={() => void handleRefresh()}
            disabled={refreshing}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-5 py-2.5 text-sm font-medium text-white transition",
              "hover:border-accent/35 hover:bg-white/[0.08] disabled:opacity-50",
              flash && "border-accent/50 ring-2 ring-accent/20"
            )}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin text-accent" />
            ) : (
              <RefreshCw className="h-4 w-4 text-accent" />
            )}
            Sync data
          </button>
          <div className="text-right font-mono text-[11px] text-ink-faint">
            {lastUpdated ? (
              <>Updated {lastUpdated.toLocaleTimeString()}</>
            ) : (
              <>Awaiting first sync…</>
            )}
          </div>
        </div>
      </div>

      {health ? (
        <div className="relative mt-8 flex flex-wrap gap-3 border-t border-white/[0.06] pt-6">
          <StatusChip
            icon={Activity}
            label="API"
            value={health.status}
            ok={health.status === "ok"}
          />
          <StatusChip
            icon={Database}
            label="Postgres"
            value={health.db_connected ? "Connected" : "Unavailable"}
            ok={health.db_connected}
          />
          <StatusChip
            icon={Cpu}
            label="Model artifacts"
            value={health.model_loaded ? "Loaded" : "Not loaded"}
            ok={health.model_loaded}
          />
          <div className="ml-auto hidden font-mono text-[11px] text-ink-faint sm:block">
            Served {health.total_predictions_served.toLocaleString()} predictions ·{" "}
            <span className="text-ink-muted">v{health.model_version}</span>
          </div>
        </div>
      ) : null}
    </motion.div>
  );
}

function StatusChip({
  icon: Icon,
  label,
  value,
  ok,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-xl border px-4 py-2.5",
        ok
          ? "border-white/[0.06] bg-white/[0.03]"
          : "border-amber-500/20 bg-amber-500/[0.06]"
      )}
    >
      <Icon className={cn("h-4 w-4", ok ? "text-accent" : "text-amber-300")} />
      <div>
        <p className="font-mono text-[9px] uppercase tracking-wider text-ink-faint">
          {label}
        </p>
        <p className="text-sm font-medium text-white">{value}</p>
      </div>
    </div>
  );
}
