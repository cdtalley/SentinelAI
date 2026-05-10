"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { ApiError, api, type TransactionRecord } from "@/lib/api";
import { Panel, PanelHeader } from "./panel";
import { TxnTable } from "./txn-table";
import { cn } from "@/lib/utils";

export function LookupClient() {
  const [id, setId] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [row, setRow] = useState<TransactionRecord | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setRow(null);
    const tid = id.trim();
    if (!tid) return;
    setLoading(true);
    try {
      const r = await api.transactionById(tid);
      setRow(r);
    } catch (e) {
      if (e instanceof ApiError) {
        setErr(`${e.status}: ${e.body?.slice(0, 400) || e.message}`);
      } else {
        setErr(e instanceof Error ? e.message : "Lookup failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-canvas-elevated/70 p-6 sm:p-8">
        <div className="pointer-events-none absolute -right-16 top-0 h-40 w-40 rounded-full bg-accent/10 blur-3xl" />
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">
          Audit retrieval
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Transaction lookup
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-muted">
          <span className="font-mono text-accent/90">GET /api/v1/predict/{"{id}"}</span> —
          returns the persisted scoring row clients would use for chargeback investigations.
        </p>
      </div>

      <Panel>
        <PanelHeader
          title="Query"
          subtitle="Paste a transaction_id emitted by the scoring sandbox or your own ingest pipeline."
        />
        <form
          onSubmit={(e) => void submit(e)}
          className="flex max-w-2xl flex-col gap-4 sm:flex-row sm:items-end"
        >
          <label className="min-w-0 flex-1 text-xs text-ink-muted">
            <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-ink-faint">
              transaction_id
            </span>
            <input
              value={id}
              onChange={(e) => setId(e.target.value)}
              placeholder="e.g. uuid from dashboard table"
              className="w-full rounded-xl border border-white/10 bg-canvas/80 px-4 py-3 font-mono text-sm text-white outline-none ring-accent/25 focus:ring-2"
            />
          </label>
          <button
            type="submit"
            disabled={loading || !id.trim()}
            className={cn(
              "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-canvas shadow-glow transition",
              "hover:bg-cyan-300 disabled:opacity-40"
            )}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Lookup
          </button>
        </form>
        {err ? (
          <pre className="mt-6 overflow-x-auto rounded-xl border border-rose-500/25 bg-rose-500/10 p-4 font-mono text-xs text-rose-100">
            {err}
          </pre>
        ) : null}
      </Panel>

      {row ? (
        <Panel>
          <PanelHeader title="Result" subtitle="Persisted explanation and structured fields." />
          <TxnTable rows={[row]} />
          {row.explanation ? (
            <div className="mt-6 rounded-xl border border-white/[0.06] bg-canvas/50 p-5 text-sm leading-relaxed text-ink-muted">
              {row.explanation}
            </div>
          ) : null}
        </Panel>
      ) : null}
    </div>
  );
}
