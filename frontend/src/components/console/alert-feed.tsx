"use client";

import { useEffect, useRef, useState } from "react";
import { Radio } from "lucide-react";
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
    <div className="rounded-xl border border-white/8 bg-canvas-elevated/60 shadow-panel">
      <div className="flex items-center justify-between border-b border-white/8 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-medium text-white">
          <Radio className="h-4 w-4 text-accent" />
          Live alerts
        </div>
        <span
          className={cn(
            "font-mono text-xs",
            status === "open" && "text-risk-ok",
            status === "connecting" && "text-risk-review",
            status === "error" && "text-risk-block",
            status === "idle" && "text-ink-faint"
          )}
        >
          {status === "open"
            ? "STREAM"
            : status === "connecting"
              ? "CONNECTING"
              : status === "error"
                ? "WS ERROR"
                : "OFFLINE"}
        </span>
      </div>
      <div className="max-h-[280px] space-y-2 overflow-y-auto p-3">
        {alerts.length === 0 ? (
          <p className="py-6 text-center text-xs text-ink-muted">
            Waiting for BLOCKED / REVIEW decisions…
          </p>
        ) : (
          alerts.map((a, i) => (
            <div
              key={`${a.transaction_id}-${a.timestamp}-${i}`}
              className="rounded-lg border border-white/6 bg-canvas/80 px-3 py-2 text-xs"
            >
              <div className="flex justify-between gap-2">
                <span className="font-mono text-accent">
                  {a.transaction_id?.slice(0, 12)}…
                </span>
                <span
                  className={cn(
                    "shrink-0 font-medium",
                    a.decision === "BLOCKED" && "text-risk-block",
                    a.decision === "REVIEW" && "text-risk-review"
                  )}
                >
                  {a.decision}
                </span>
              </div>
              <div className="mt-1 text-ink-muted">
                ${a.amount?.toFixed(2)} · p={((a.fraud_probability ?? 0) * 100).toFixed(1)}%
                {a.top_risk_signal ? ` · ${a.top_risk_signal}` : ""}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
