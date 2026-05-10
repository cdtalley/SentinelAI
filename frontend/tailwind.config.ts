import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: "#070a12",
          elevated: "#0c101c",
          subtle: "#111827",
        },
        accent: {
          DEFAULT: "#22d3ee",
          muted: "#0891b2",
          glow: "rgba(34, 211, 238, 0.15)",
        },
        ink: {
          DEFAULT: "#e2e8f0",
          muted: "#94a3b8",
          faint: "#64748b",
        },
        risk: {
          block: "#f43f5e",
          review: "#fbbf24",
          ok: "#34d399",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to bottom, transparent, #070a12), linear-gradient(90deg, rgba(148,163,184,0.06) 1px, transparent 1px), linear-gradient(rgba(148,163,184,0.06) 1px, transparent 1px)",
        "hero-glow":
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(34,211,238,0.25), transparent)",
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(148,163,184,0.08), 0 24px 48px -12px rgba(0,0,0,0.45)",
        glow: "0 0 40px -10px rgba(34, 211, 238, 0.35)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
