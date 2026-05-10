import Link from "next/link";
import { ApiLivePill } from "@/components/marketing/api-live-pill";

export default function MarketingLayout({
  children,
}: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-hero-glow bg-grid-fade">
      <header className="fixed top-0 z-50 w-full border-b border-white/5 bg-canvas/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2 font-mono text-sm tracking-tight text-ink">
            <span className="h-2 w-2 rounded-full bg-accent shadow-glow" />
            SentinelAI
          </Link>
          <div className="flex items-center gap-4">
            <ApiLivePill />
          <nav className="flex items-center gap-6 text-sm text-ink-muted">
            <Link href="/dashboard" className="transition hover:text-accent">
              Console
            </Link>
            <Link
              href="/lookup"
              className="transition hover:text-accent"
            >
              Lookup
            </Link>
            <Link
              href="/model-health"
              className="transition hover:text-accent"
            >
              Model health
            </Link>
          </nav>
          </div>
        </div>
      </header>
      <main className="pt-14">{children}</main>
    </div>
  );
}
