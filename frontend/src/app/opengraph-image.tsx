import { ImageResponse } from "next/og";

export const runtime = "edge";

export const alt = "SentinelAI — fraud intelligence console";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "linear-gradient(145deg, #070a12 0%, #0c101c 45%, #082f35 100%)",
          padding: 56,
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            color: "#22d3ee",
            fontSize: 22,
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 999,
              background: "#22d3ee",
              boxShadow: "0 0 24px #22d3ee",
            }}
          />
          SentinelAI
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div
            style={{
              fontSize: 64,
              fontWeight: 700,
              color: "#f8fafc",
              lineHeight: 1.05,
              maxWidth: 900,
              letterSpacing: "-0.03em",
            }}
          >
            Real-time fraud intelligence
          </div>
          <div style={{ fontSize: 28, color: "#94a3b8", maxWidth: 820, lineHeight: 1.4 }}>
            Next.js console · FastAPI · Postgres · WebSockets · SHAP · production ops UX
          </div>
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 20,
            color: "#64748b",
          }}
        >
          <span>Portfolio / Upwork catalog build</span>
          <span style={{ color: "#22d3ee", fontWeight: 600 }}>Full-stack demo</span>
        </div>
      </div>
    ),
    { ...size }
  );
}
