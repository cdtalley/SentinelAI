import type { TransactionRecord } from "@/lib/api";
import { cn } from "@/lib/utils";

function decisionPill(decision: string) {
  const d = decision.toUpperCase();
  return cn(
    "inline-flex rounded-md px-2 py-0.5 font-mono text-xs font-medium",
    d === "BLOCKED" && "bg-risk-block/15 text-risk-block",
    d === "REVIEW" && "bg-risk-review/15 text-risk-review",
    d === "APPROVED" && "bg-risk-ok/15 text-risk-ok"
  );
}

export function TxnTable({ rows }: { rows: TransactionRecord[] }) {
  if (rows.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-ink-muted">
        No scored transactions yet. Run a prediction from the sandbox below.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-white/8 text-xs uppercase tracking-wider text-ink-faint">
            <th className="pb-3 pr-4 font-medium">ID</th>
            <th className="pb-3 pr-4 font-medium">Amount</th>
            <th className="pb-3 pr-4 font-medium">P(fraud)</th>
            <th className="pb-3 pr-4 font-medium">Decision</th>
            <th className="pb-3 pr-4 font-medium">Model</th>
            <th className="pb-3 font-medium">Predicted</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {rows.map((r) => (
            <tr
              key={r.transaction_id}
              className="text-ink transition hover:bg-white/[0.02]"
            >
              <td className="max-w-[180px] truncate py-3 pr-4 font-mono text-xs text-accent">
                {r.transaction_id}
              </td>
              <td className="py-3 pr-4 tabular-nums">${r.amount.toFixed(2)}</td>
              <td className="py-3 pr-4 tabular-nums">
                {(r.fraud_probability * 100).toFixed(1)}%
              </td>
              <td className="py-3 pr-4">
                <span className={decisionPill(r.decision)}>{r.decision}</span>
              </td>
              <td className="py-3 pr-4 text-ink-muted">{r.model_used}</td>
              <td className="py-3 text-xs text-ink-muted">
                {new Date(r.predicted_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
