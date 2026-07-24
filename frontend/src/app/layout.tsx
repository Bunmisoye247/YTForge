import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppQueryProvider } from "@/lib/query-client";
import { AppBootstrap } from "@/components/layout/AppBootstrap";
import { Toaster } from "@/components/ui/Toast";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "YTForge",
  description: "AI-powered YouTube automation platform",
};

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
    <html lang="en" suppressHydrationWarning>
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
