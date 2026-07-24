"use client";

import { useEffect } from "react";
import { useHydrateSession } from "@/lib/hooks/use-auth";
import { hydrateTheme } from "@/lib/stores/theme-store";

/** Runs once on mount: syncs the theme store to match the class the inline
 * head script already applied to <html>, and attempts a silent session
 * refresh using the httpOnly refresh cookie. Rendered once in the root
 * layout so both auth and dashboard routes see the result. */
export function AppBootstrap() {
  useHydrateSession();

  useEffect(() => {
    hydrateTheme();
  }, []);

  return null;
}
