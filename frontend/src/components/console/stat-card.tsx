import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  className,
}: {
  label: string;
  value: string;
  hint?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/8 bg-canvas-elevated/60 p-5 shadow-panel",
        className
      )}
    >
      <p className="font-mono text-xs uppercase tracking-wider text-ink-faint">
        {label}
      </p>
      <p className="mt-2 font-mono text-2xl font-semibold tabular-nums text-white">
        {value}
      </p>
      {hint ? (
        <p className="mt-1 text-xs text-ink-muted">{hint}</p>
      ) : null}
    </div>
  );
}
