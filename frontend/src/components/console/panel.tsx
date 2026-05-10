import { cn } from "@/lib/utils";

export function Panel({
  children,
  className,
  bleed = false,
}: {
  children: React.ReactNode;
  className?: string;
  bleed?: boolean;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/[0.07] bg-gradient-to-b from-white/[0.04] to-transparent shadow-panel",
        "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-accent/40 before:to-transparent",
        className
      )}
    >
      <div className={cn(!bleed && "p-5 sm:p-6")}>{children}</div>
    </div>
  );
}

export function PanelHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col gap-3 border-b border-white/[0.06] pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 className="font-mono text-[11px] font-medium uppercase tracking-[0.2em] text-accent/90">
          {title}
        </h2>
        {subtitle ? (
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-ink-muted">
            {subtitle}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
