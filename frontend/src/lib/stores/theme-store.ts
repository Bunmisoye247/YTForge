import { create } from "zustand";

export type Theme = "light" | "dark";

const STORAGE_KEY = "ytforge-theme";

function applyThemeClass(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

function readInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

type ThemeState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: "light",
  setTheme: (theme) => {
    window.localStorage.setItem(STORAGE_KEY, theme);
    applyThemeClass(theme);
    set({ theme });
  },
  toggleTheme: () => get().setTheme(get().theme === "dark" ? "light" : "dark"),
}));

/** Called once from a client-only effect in the root layout after mount. */
export function hydrateTheme() {
  const theme = readInitialTheme();
  applyThemeClass(theme);
  useThemeStore.setState({ theme });
}
