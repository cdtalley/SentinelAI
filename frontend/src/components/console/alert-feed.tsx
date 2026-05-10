"use client";

import { useEffect, useRef, useState } from "react";
import { Radio, Zap } from "lucide-react";
import { getWsAlertsUrl } from "@/lib/config";
import { cn } from "@/lib/utils";

export type AlertMsg = {
  type: string;
  transaction_id?: string;
  amount?: number;
  fraud_probability?: number;
  decision?: string;
  top_risk_signal?: string;
  timestamp?: string;
};

export function AlertFeed() {
  const [status, setStatus] = useState<"idle" | "connecting" | "open" | "error">(
    "idle"
  );
  const [alerts, setAlerts] = useState<AlertMsg[]>([]);
  const seen = useRef(new Set<string>());

  useEffect(() => {
    let alive = true;
    const url = getWsAlertsUrl();
    setStatus("connecting");
    const ws = new WebSocket(url);

    ws.onopen = () => {
      if (!alive) return;
      setStatus("open");
      seen.current.clear();
    };

    ws.onmessage = (ev) => {
      if (!alive) return;
      try {
        const data = JSON.parse(ev.data as string) as AlertMsg & {
          payload?: AlertMsg[];
        };
        if (data.type === "history" && Array.isArray(data.payload)) {
          setAlerts(data.payload.slice(-20).reverse());
          return;
        }
        if (data.type === "alert") {
          const key = `${data.transaction_id}-${data.timestamp}`;
          if (seen.current.has(key)) return;
          seen.current.add(key);
          setAlerts((prev) => [{ ...data }, ...prev].slice(0, 50));
        }
      } catch {
        /* ignore parse errors */
      }
    };

    ws.onerror = () => {
      if (alive) setStatus("error");
    };
    ws.onclose = () => {
      if (alive) setStatus("idle");
    };

    return () => {
      alive = false;
      ws.close();
    };
  }, []);

  return (
    <div className="flex h-full min-h-[320px] flex-col overflow-hidden rounded-2xl border border-white/[0.07] bg-gradient-to-b from-white/[0.04] to-transparent shadow-panel">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3.5 sm:px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent/20 bg-accent/10">
            <Zap className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Incident stream</p>
            <p className="font-mono text-[10px] uppercase tracking-wider text-ink-faint">
              WebSocket · /api/v1/ws/alerts
            </p>
          </div>
        </div>
        <span
          className={cn(
            "rounded-full border px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider",
            status === "open" &&
              "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
            status === "connecting" &&
              "border-amber-500/30 bg-amber-500/10 text-amber-200",
            status === "error" && "border-rose-500/30 bg-rose-500/10 text-rose-200",
            status === "idle" && "border-white/10 text-ink-faint"
          )}
        >
          <Radio className="mr-1 inline h-3 w-3" />
          {status === "open"
            ? "Live"
            : status === "connecting"
              ? "Linking"
              : status === "error"
                ? "Error"
                : "Idle"}
        </span>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-3 sm:p-4">
        {alerts.length === 0 ? (
          <div className="flex h-full min-h-[200px] flex-col items-center justify-center gap-2 px-4 text-center">
            <p className="text-xs text-ink-muted">
              Listening for <span className="text-risk-block">BLOCKED</span> and{" "}
              <span className="text-risk-review">REVIEW</span> decisions. Score a
              high-risk transaction in the sandbox to populate this feed for your
              demo recording.
            </p>
          </div>
        ) : (
          alerts.map((a, i) => (
            <div
              key={`${a.transaction_id}-${a.timestamp}-${i}`}
              className={cn(
                "rounded-xl border border-white/[0.06] bg-canvas/60 px-3.5 py-3 text-xs backdrop-blur-sm",
                "border-l-[3px]",
                a.decision === "BLOCKED" && "border-l-rose-400",
                a.decision === "REVIEW" && "border-l-amber-400",
                !a.decision && "border-l-slate-500"
              )}
            >
              <div className="flex justify-between gap-2">
                <span className="truncate font-mono text-[11px] text-accent">
                  {a.transaction_id}
                </span>
                <span
                  className={cn(
                    "shrink-0 font-mono text-[10px] font-bold uppercase tracking-wide",
                    a.decision === "BLOCKED" && "text-rose-300",
                    a.decision === "REVIEW" && "text-amber-200"
                  )}
                >
                  {a.decision}
                </span>
              </div>
              <div className="mt-1.5 text-ink-muted">
                <span className="tabular-nums text-ink">
                  ${a.amount?.toFixed(2) ?? "—"}
                </span>
                {" · "}
                <span className="tabular-nums">
                  p={((a.fraud_probability ?? 0) * 100).toFixed(1)}%
                </span>
                {a.top_risk_signal ? (
                  <>
                    {" · "}
                    <span className="text-ink-faint">{a.top_risk_signal}</span>
                  </>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
