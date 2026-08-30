import type { Metadata, Viewport } from "next";
import { Inter, Fraunces } from "next/font/google";

import { QueryProvider } from "@/lib/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600"],
});

export const metadata: Metadata = {
  title: "AMH Hospitality — PMS",
  description: "Système de gestion hôtelière — AMH Hospitality (Riads Marrakech)",
  // Mobile Housekeeping (Sprint 6, D13) : PWA installable dans ce même
  // Next.js app plutôt qu'une app React Native/Expo séparée — voir D13.
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: "AMH Housekeeping" },
};

export const viewport: Viewport = {
  themeColor: "#1a1512",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={cn(inter.variable, fraunces.variable)} suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider>
          <QueryProvider>
            <TooltipProvider>
              {children}
              <Toaster position="top-right" />
            </TooltipProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
