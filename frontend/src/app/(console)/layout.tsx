import type { Metadata } from "next";
import { Shell } from "@/components/shell";

export const metadata: Metadata = {
  title: "Console",
  description:
    "Live fraud operations: KPIs, decision distribution, WebSocket alerts, scoring sandbox.",
};

export default function ConsoleLayout({
  children,
}: { children: React.ReactNode }) {
  return <Shell>{children}</Shell>;
}
