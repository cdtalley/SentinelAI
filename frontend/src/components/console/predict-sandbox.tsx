"use client";

import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import {
  ApiError,
  api,
  minimalTransactionInput,
  type PredictionWithExplanation,
} from "@/lib/api";
import { ShapBars } from "./shap-bars";
import { cn } from "@/lib/utils";

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
    <div className="rounded-xl border border-white/8 bg-canvas-elevated/60 p-5 shadow-panel">
      <h3 className="text-sm font-medium text-white">Score sandbox</h3>
      <p className="mt-1 text-xs text-ink-muted">
        POST /api/v1/predict with a valid feature vector — persists audit row when DB is up.
      </p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="text-xs text-ink-muted">
          <span className="mb-1 block font-mono uppercase tracking-wider">
            Amount (USD)
          </span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-32 rounded-lg border border-white/10 bg-canvas px-3 py-2 font-mono text-sm text-white outline-none ring-accent/30 focus:ring-2"
          />
        </label>
        <button
          type="button"
          onClick={() => void run()}
          disabled={loading}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-canvas transition hover:bg-cyan-300 disabled:opacity-50"
          )}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Run score
        </button>
      </div>
      {err ? (
        <pre className="mt-4 overflow-x-auto rounded-lg bg-risk-block/10 p-3 font-mono text-xs text-risk-block">
          {err}
        </pre>
      ) : null}
      {result ? (
        <div className="mt-6 space-y-4 border-t border-white/8 pt-6">
          <div className="flex flex-wrap gap-4 text-sm">
            <div>
              <span className="text-ink-faint">Decision</span>
              <p className="font-mono text-lg text-white">{result.decision}</p>
            </div>
            <div>
              <span className="text-ink-faint">P(fraud)</span>
              <p className="font-mono text-lg text-white">
                {(result.fraud_probability * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <span className="text-ink-faint">Latency</span>
              <p className="font-mono text-lg text-white">
                {result.processing_time_ms.toFixed(1)} ms
              </p>
            </div>
            <div>
              <span className="text-ink-faint">Model</span>
              <p className="font-mono text-lg text-accent">{result.model_used}</p>
            </div>
          </div>
          {result.explanation ? (
            <div className="rounded-lg border border-white/6 bg-canvas/50 p-3 text-xs leading-relaxed text-ink-muted">
              {result.explanation}
            </div>
          ) : null}
          <ShapBars features={result.top_shap_features} />
        </div>
      ) : null}
    </div>
  );
}
