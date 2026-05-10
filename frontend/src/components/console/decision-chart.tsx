"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const COLORS: Record<string, string> = {
  BLOCKED: "#fb7185",
  REVIEW: "#fcd34d",
  APPROVED: "#6ee7b7",
};

export function DecisionChart({
  blocked,
  review,
  approved,
}: {
  blocked: number;
  review: number;
  approved: number;
}) {
  const raw = [
    { name: "BLOCKED", value: blocked },
    { name: "REVIEW", value: review },
    { name: "APPROVED", value: approved },
  ];
  const total = blocked + review + approved;
  const data = raw.filter((d) => d.value > 0);

  if (data.length === 0 || total === 0) {
    return (
      <div className="flex min-h-[260px] flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-white/10 bg-canvas/40 px-6 py-12 text-center">
        <p className="max-w-sm text-sm text-ink-muted">
          No decisions in the rolling window yet. Use{" "}
          <span className="font-mono text-accent">Score sandbox</span> below to
          generate live traffic — watch this chart and the alert stream update
          instantly.
        </p>
      </div>
    );
  }

  return (
    <div className="relative min-h-[260px] w-full rounded-2xl border border-white/[0.07] bg-gradient-to-b from-white/[0.03] to-transparent p-4 sm:p-6">
      <div className="relative h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={58}
              outerRadius={82}
              paddingAngle={2}
              stroke="rgba(7,10,18,0.9)"
              strokeWidth={2}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[entry.name] ?? "#64748b"}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#0c101c",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "10px",
                fontSize: "12px",
                boxShadow: "0 16px 40px rgba(0,0,0,0.45)",
              }}
              labelStyle={{ color: "#e2e8f0", fontWeight: 600 }}
              formatter={(value: number, name: string) => [
                `${value} (${((value / total) * 100).toFixed(1)}%)`,
                name,
              ]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="font-mono text-3xl font-bold tabular-nums text-white">
              {total.toLocaleString()}
            </p>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.2em] text-ink-faint">
              In window
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 border-t border-white/[0.06] pt-4">
        {raw.map((row) => (
          <div key={row.name} className="flex items-center gap-2">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: COLORS[row.name] }}
            />
            <span className="font-mono text-xs text-ink-muted">{row.name}</span>
            <span className="font-mono text-xs tabular-nums text-white">
              {row.value}{" "}
              <span className="text-ink-faint">
                ({total ? ((row.value / total) * 100).toFixed(0) : 0}%)
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
