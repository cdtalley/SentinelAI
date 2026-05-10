import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

const site =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ||
  "http://localhost:3010";

export const metadata: Metadata = {
  metadataBase: new URL(site),
  title: {
    default: "SentinelAI | Fraud intelligence console",
    template: "%s · SentinelAI",
  },
  description:
    "Enterprise-grade fraud console: live KPIs, WebSocket alerts, SHAP scoring sandbox, drift PSI — FastAPI + Postgres + Next.js.",
  keywords: [
    "fraud detection",
    "MLOps",
    "FastAPI",
    "Next.js",
    "risk operations",
    "SHAP",
    "real-time scoring",
  ],
  authors: [{ name: "SentinelAI" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "SentinelAI",
    title: "SentinelAI | Fraud intelligence console",
    description:
      "Portfolio-grade ops console: metrics, decision mix, live alerts, and scoring demo wired to your ML API.",
  },
  twitter: {
    card: "summary_large_image",
    title: "SentinelAI | Fraud intelligence console",
    description:
      "Portfolio-grade ops console for real-time fraud decisions and drift governance.",
  },
};

export const viewport: Viewport = {
  themeColor: "#070a12",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
