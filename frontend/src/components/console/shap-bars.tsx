"use client";

import type { SHAPFeature } from "@/lib/api";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ShapBars({ features }: { features: SHAPFeature[] }) {
  const data = [...features]
    .sort((a, b) => b.abs_impact - a.abs_impact)
    .slice(0, 8)
    .map((f) => ({
      name: f.feature_name.length > 18 ? `${f.feature_name.slice(0, 16)}…` : f.feature_name,
      impact: f.abs_impact,
      direction: f.direction,
    }));

  if (data.length === 0) return null;

  return (
    <div className="h-[240px] w-full rounded-xl border border-white/8 bg-canvas-elevated/40 p-2">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            width={100}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            contentStyle={{
              background: "#0c101c",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              fontSize: "11px",
            }}
          />
          <Bar dataKey="impact" fill="#22d3ee" radius={[0, 4, 4, 0]} maxBarSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
