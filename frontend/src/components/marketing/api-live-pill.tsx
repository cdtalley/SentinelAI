"use client";

import { useEffect, useState } from "react";
import { getApiBase } from "@/lib/config";
import { cn } from "@/lib/utils";

type State = "checking" | "live" | "down";

export function ApiLivePill() {
  const [state, setState] = useState<State>("checking");

  useEffect(() => {
    let cancelled = false;

    async function ping() {
      try {
        const res = await fetch(`${getApiBase()}/api/v1/health/live`, {
          cache: "no-store",
        });
        if (!cancelled) setState(res.ok ? "live" : "down");
      } catch {
        if (!cancelled) setState("down");
      }
    }

    void ping();
    const id = setInterval(() => void ping(), 20_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div
      className={cn(
        "hidden items-center gap-2 rounded-full border px-3 py-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider sm:flex",
        state === "live" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
        state === "down" && "border-rose-500/30 bg-rose-500/10 text-rose-200",
        state === "checking" && "border-white/10 text-ink-muted"
      )}
      title={`API base: ${getApiBase()}`}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          state === "live" && "animate-pulse bg-emerald-400",
          state === "down" && "bg-rose-400",
          state === "checking" && "bg-slate-500"
        )}
      />
      API {state === "live" ? "live" : state === "down" ? "offline" : "…"}
    </div>
  );
}
