import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import { AppQueryProvider } from "@/lib/query-client";
import { AppBootstrap } from "@/components/layout/AppBootstrap";
import { Toaster } from "@/components/ui/Toast";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "YTForge",
  description: "AI-powered YouTube automation platform",
};

// Self-hosted via next/font (no external Google Fonts request at
// runtime — fonts are bundled at build time) and exposed as CSS
// variables that globals.css's `--font-display`/`--font-body`/
// `--font-mono` theme tokens point at.
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-space-grotesk",
});
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains-mono",
});

// Runs before hydration to apply the stored/system theme without a
// flash-of-wrong-theme (see lib/stores/theme-store.ts's hydrateTheme,
// which this mirrors synchronously for the very first paint).
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = window.localStorage.getItem("ytforge-theme");
    var theme = stored === "light" || stored === "dark"
      ? stored
      : (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    if (theme === "dark") document.documentElement.classList.add("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${spaceGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body suppressHydrationWarning>
        <AppQueryProvider>
          <AppBootstrap />
          {children}
          <Toaster />
        </AppQueryProvider>
      </body>
    </html>
  );
}
