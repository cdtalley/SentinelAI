"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  Layers,
  Radio,
  Shield,
  Zap,
} from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Sub-10ms scoring",
    body: "Vectorized inference path with structured latency telemetry (p95, error rate).",
  },
  {
    icon: Radio,
    title: "Live alert stream",
    body: "WebSocket channel for high-risk decisions — ops sees incidents as they happen.",
  },
  {
    icon: Layers,
    title: "Drift & PSI",
    body: "Population stability and per-feature drift signals for governance and MLOps.",
  },
  {
    icon: Shield,
    title: "API-key auth",
    body: "Production-ready gates: rate limits, correlation IDs, health/readiness probes.",
  },
];

export function MarketingHero() {
  return (
    <div className="relative">
      <section className="mx-auto max-w-6xl px-4 pb-24 pt-20 sm:px-6 sm:pt-28">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="max-w-3xl"
        >
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 font-mono text-xs text-accent">
            <Activity className="h-3.5 w-3.5" />
            Production fraud intelligence stack
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl sm:leading-[1.1]">
            Real-time decisions with{" "}
            <span className="bg-gradient-to-r from-accent to-emerald-400 bg-clip-text text-transparent">
              operational clarity
            </span>
            .
          </h1>
          <p className="mt-6 text-lg leading-relaxed text-ink-muted">
            SentinelAI pairs a FastAPI scoring plane with Postgres-backed
            transactions, SHAP-ready explanations, and a console built for how
            risk teams actually work — not a toy demo.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-canvas shadow-glow transition hover:bg-cyan-300"
            >
              Open console
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/model-health"
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-5 py-2.5 text-sm text-ink transition hover:border-accent/40 hover:text-white"
            >
              Model health
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.12 }}
          className="mt-20 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {features.map((f) => (
            <div
              key={f.title}
              className="group rounded-xl border border-white/8 bg-canvas-elevated/80 p-5 shadow-panel backdrop-blur-sm transition hover:border-accent/25"
            >
              <f.icon className="h-8 w-8 text-accent opacity-90 transition group-hover:scale-105" />
              <h3 className="mt-4 font-medium text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                {f.body}
              </p>
            </div>
          ))}
        </motion.div>
      </section>

      <section className="border-t border-white/5 bg-canvas-elevated/50 py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="font-mono text-xs uppercase tracking-widest text-ink-faint">
            Stack signal
          </p>
          <p className="mt-2 max-w-2xl text-ink-muted">
            Next.js 14 · TypeScript · Tailwind · Recharts · FastAPI · scikit-learn
            · Postgres · Alembic · Docker · GitHub Actions
          </p>
        </div>
      </section>
    </div>
  );
}
