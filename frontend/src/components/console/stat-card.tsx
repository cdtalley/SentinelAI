import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  className,
  skeleton,
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  className?: string;
  skeleton?: boolean;
}) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-white/[0.07] bg-gradient-to-br from-white/[0.05] to-transparent p-5 shadow-panel",
        "transition hover:border-accent/20 hover:shadow-[0_0_40px_-12px_rgba(34,211,238,0.15)]",
        className
      )}
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-accent/5 blur-2xl transition group-hover:bg-accent/10" />
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[10px] font-medium uppercase tracking-[0.18em] text-ink-faint">
            {label}
          </p>
          {skeleton ? (
            <div className="mt-3 space-y-2">
              <div className="h-8 w-24 animate-pulse rounded-md bg-white/10" />
              <div className="h-3 w-40 animate-pulse rounded bg-white/5" />
            </div>
          ) : (
            <>
              <p className="mt-2 truncate font-mono text-2xl font-semibold tabular-nums tracking-tight text-white sm:text-[1.65rem]">
                {value}
              </p>
              {hint ? (
                <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-ink-muted">
                  {hint}
                </p>
              ) : null}
            </>
          )}
        </div>
        {Icon && !skeleton ? (
          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-2 text-accent">
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
      </div>
    </div>
  );
}
