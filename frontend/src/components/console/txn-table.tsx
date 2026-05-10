import type { TransactionRecord } from "@/lib/api";
import { cn } from "@/lib/utils";

function decisionPill(decision: string) {
  const d = decision.toUpperCase();
  return cn(
    "inline-flex rounded-md border px-2 py-0.5 font-mono text-[11px] font-semibold tracking-wide",
    d === "BLOCKED" &&
      "border-rose-500/30 bg-rose-500/10 text-rose-200",
    d === "REVIEW" &&
      "border-amber-500/30 bg-amber-500/10 text-amber-100",
    d === "APPROVED" &&
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
  );
}

export function TxnTable({ rows }: { rows: TransactionRecord[] }) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] py-16 text-center">
        <p className="mx-auto max-w-md text-sm text-ink-muted">
          No rows returned. Start the API, ensure Postgres is reachable, then run
          a score from the sandbox — this table reads the same persisted audit trail
          your production risk team would rely on.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-white/[0.06]">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead>
            <tr className="border-b border-white/[0.08] bg-white/[0.03] font-mono text-[10px] uppercase tracking-[0.15em] text-ink-faint">
              <th className="px-4 py-3.5 font-medium">Transaction</th>
              <th className="px-4 py-3.5 font-medium">Amount</th>
              <th className="px-4 py-3.5 font-medium">Risk</th>
              <th className="px-4 py-3.5 font-medium">Decision</th>
              <th className="px-4 py-3.5 font-medium">Model</th>
              <th className="px-4 py-3.5 font-medium">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.05]">
            {rows.map((r) => (
              <tr
                key={r.transaction_id}
                className="text-ink transition-colors hover:bg-white/[0.03]"
              >
                <td className="max-w-[200px] truncate px-4 py-3.5 font-mono text-xs text-accent">
                  {r.transaction_id}
                </td>
                <td className="px-4 py-3.5 tabular-nums text-white">
                  ${r.amount.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td className="px-4 py-3.5 tabular-nums text-ink-muted">
                  <span className="text-white">
                    {(r.fraud_probability * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <span className={decisionPill(r.decision)}>{r.decision}</span>
                </td>
                <td className="px-4 py-3.5 font-mono text-xs text-ink-muted">
                  {r.model_used}
                </td>
                <td className="px-4 py-3.5 font-mono text-[11px] text-ink-faint">
                  {new Date(r.predicted_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
