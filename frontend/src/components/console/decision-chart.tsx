"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const COLORS: Record<string, string> = {
  BLOCKED: "#f43f5e",
  REVIEW: "#fbbf24",
  APPROVED: "#34d399",
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
  const data = [
    { name: "BLOCKED", value: blocked },
    { name: "REVIEW", value: review },
    { name: "APPROVED", value: approved },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex h-[220px] items-center justify-center rounded-xl border border-white/8 bg-canvas-elevated/40 text-sm text-ink-muted">
        No decisions in the rolling window yet.
      </div>
    );
  }

  return (
    <div className="h-[220px] w-full rounded-xl border border-white/8 bg-canvas-elevated/40 p-2">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={52}
            outerRadius={72}
            paddingAngle={2}
          >
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={COLORS[entry.name] ?? "#64748b"}
                stroke="rgba(0,0,0,0.2)"
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#0c101c",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#e2e8f0" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
