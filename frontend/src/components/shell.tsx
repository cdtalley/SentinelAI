"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  LayoutDashboard,
  Microscope,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/lookup", label: "Lookup", icon: Search },
  { href: "/model-health", label: "Model health", icon: Microscope },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-canvas bg-grid-fade">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-56 border-r border-white/8 bg-canvas-elevated/95 backdrop-blur-xl lg:block">
        <div className="flex h-14 items-center gap-2 border-b border-white/8 px-4 font-mono text-sm text-ink">
          <span className="h-2 w-2 rounded-full bg-accent shadow-glow" />
          SentinelAI
        </div>
        <nav className="space-y-0.5 p-3">
          {nav.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                  active
                    ? "bg-white/[0.06] text-white"
                    : "text-ink-muted hover:bg-white/[0.04] hover:text-ink"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t border-white/8 p-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs text-ink-faint transition hover:text-ink-muted"
          >
            <Activity className="h-3.5 w-3.5" />
            Product overview
          </Link>
        </div>
      </aside>

      <div className="flex flex-1 flex-col lg:pl-56">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-white/8 bg-canvas/90 px-4 backdrop-blur-md lg:hidden">
          <span className="font-mono text-sm text-ink">SentinelAI</span>
          <nav className="flex gap-3 text-xs">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-ink-muted",
                  pathname === item.href && "text-accent"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="flex-1 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
