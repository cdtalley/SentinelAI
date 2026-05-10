"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Play, Wand2 } from "lucide-react";
import {
  ApiError,
  api,
  minimalTransactionInput,
  type PredictionWithExplanation,
} from "@/lib/api";
import { ShapBars } from "./shap-bars";
import { cn } from "@/lib/utils";

function decisionBadgeClass(d: string) {
  const x = d.toUpperCase();
  return cn(
    "inline-flex items-center rounded-lg border px-4 py-2 font-mono text-sm font-bold uppercase tracking-widest",
    x === "BLOCKED" && "border-rose-400/40 bg-rose-500/15 text-rose-100 shadow-[0_0_24px_-4px_rgba(244,63,94,0.35)]",
    x === "REVIEW" && "border-amber-400/40 bg-amber-500/15 text-amber-50 shadow-[0_0_24px_-4px_rgba(251,191,36,0.25)]",
    x === "APPROVED" && "border-emerald-400/40 bg-emerald-500/15 text-emerald-50"
  );
}

export function PredictSandbox({ onScored }: { onScored?: () => void }) {
  const [amount, setAmount] = useState("249.0");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionWithExplanation | null>(null);

  async function run() {
    setErr(null);
    setLoading(true);
    setResult(null);
    try {
      const amt = parseFloat(amount);
      if (!Number.isFinite(amt) || amt <= 0) {
        setErr("Amount must be a positive number.");
        setLoading(false);
        return;
      }
      const payload = minimalTransactionInput({
        amount: amt,
        time: (Date.now() / 1000) % 1_000_000,
        v1: amt / 1000,
        v2: 0.02,
      });
      const res = await api.predict(payload);
      setResult(res);
      onScored?.();
    } catch (e) {
      if (e instanceof ApiError) {
        setErr(`${e.status}: ${e.body?.slice(0, 200) || e.message}`);
      } else {
        setErr(e instanceof Error ? e.message : "Request failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-gradient-to-br from-violet-500/[0.07] via-transparent to-accent/[0.06] p-6 sm:p-8">
      <div className="pointer-events-none absolute -right-20 top-0 h-40 w-40 rounded-full bg-accent/10 blur-3xl" />
      <div className="relative grid gap-8 lg:grid-cols-2 lg:gap-10">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
            <Wand2 className="h-3 w-3 text-accent" />
            Client demo · one click
          </div>
          <h3 className="text-xl font-semibold text-white">Score sandbox</h3>
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">
            Drives <span className="font-mono text-accent/90">POST /api/v1/predict</span>{" "}
            with a valid 28-D feature vector. Persists to Postgres when configured —
            the same path a mobile or core-banking client would use.
          </p>
          <div className="mt-6 flex flex-wrap items-end gap-4">
            <label className="text-xs text-ink-muted">
              <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-ink-faint">
                Amount (USD)
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-36 rounded-xl border border-white/10 bg-canvas/80 px-4 py-2.5 font-mono text-sm text-white outline-none ring-accent/25 focus:ring-2"
              />
            </label>
            <button
              type="button"
              onClick={() => void run()}
              disabled={loading}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-2.5 text-sm font-semibold text-canvas shadow-glow transition",
                "hover:bg-cyan-300 disabled:opacity-50"
              )}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4 fill-current" />
              )}
              Run live score
            </button>
          </div>
          {err ? (
            <pre className="mt-5 overflow-x-auto rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 font-mono text-xs text-rose-100">
              {err}
            </pre>
          ) : null}
        </div>

        <div className="relative min-h-[200px] rounded-2xl border border-white/[0.06] bg-black/25 p-5 sm:p-6">
          <AnimatePresence mode="wait">
            {!result && !loading && !err ? (
              <motion.div
                key="hint"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-full min-h-[180px] flex-col items-center justify-center gap-3 text-center"
              >
                <p className="max-w-xs text-sm text-ink-muted">
                  Output appears here — ideal for screen recordings and live client
                  walkthroughs.
                </p>
              </motion.div>
            ) : null}
            {loading ? (
              <motion.div
                key="load"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex min-h-[180px] flex-col items-center justify-center gap-3"
              >
                <Loader2 className="h-10 w-10 animate-spin text-accent" />
                <p className="font-mono text-xs text-ink-muted">Scoring…</p>
              </motion.div>
            ) : null}
            {result ? (
              <motion.div
                key="out"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-5"
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <span className={decisionBadgeClass(result.decision)}>
                    {result.decision}
                  </span>
                  <div className="text-right">
                    <p className="font-mono text-[10px] uppercase tracking-widest text-ink-faint">
                      Fraud probability
                    </p>
                    <p className="font-mono text-3xl font-bold tabular-nums text-white">
                      {(result.fraud_probability * 100).toFixed(2)}
                      <span className="text-lg text-ink-muted">%</span>
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2">
                    <p className="font-mono text-[9px] uppercase text-ink-faint">
                      Latency
                    </p>
                    <p className="font-mono text-lg text-white">
                      {result.processing_time_ms.toFixed(1)} ms
                    </p>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2">
                    <p className="font-mono text-[9px] uppercase text-ink-faint">
                      Model
                    </p>
                    <p className="font-mono text-lg text-accent">{result.model_used}</p>
                  </div>
                </div>
                {result.explanation ? (
                  <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 text-xs leading-relaxed text-ink-muted">
                    {result.explanation}
                  </div>
                ) : null}
                <ShapBars features={result.top_shap_features} />
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
