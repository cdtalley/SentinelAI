"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { ApiError, api, type TransactionRecord } from "@/lib/api";
import { PageHeader } from "./page-header";
import { TxnTable } from "./txn-table";

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
    <div>
      <PageHeader
        title="Transaction lookup"
        description="GET /api/v1/predict/{transaction_id} — persisted audit trail from Postgres."
      />
      <form
        onSubmit={(e) => void submit(e)}
        className="mb-8 flex max-w-xl flex-col gap-3 sm:flex-row sm:items-end"
      >
        <label className="flex-1 text-xs text-ink-muted">
          <span className="mb-1 block font-mono uppercase tracking-wider text-ink-faint">
            transaction_id
          </span>
          <input
            value={id}
            onChange={(e) => setId(e.target.value)}
            placeholder="uuid from a prior score"
            className="w-full rounded-lg border border-white/10 bg-canvas-elevated px-3 py-2.5 font-mono text-sm text-white outline-none ring-accent/30 focus:ring-2"
          />
        </label>
        <button
          type="submit"
          disabled={loading || !id.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-canvas transition hover:bg-cyan-300 disabled:opacity-40"
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
        <pre className="mb-6 overflow-x-auto rounded-lg bg-risk-block/10 p-4 font-mono text-xs text-risk-block">
          {err}
        </pre>
      ) : null}
      {row ? (
        <div className="rounded-xl border border-white/8 bg-canvas-elevated/60 p-4 shadow-panel">
          <TxnTable rows={[row]} />
          {row.explanation ? (
            <div className="mt-4 rounded-lg border border-white/6 bg-canvas/50 p-4 text-sm leading-relaxed text-ink-muted">
              {row.explanation}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
