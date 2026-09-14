import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

const storageKey = "faircourt_theme";

function preferredTheme(): Theme {
  const saved = localStorage.getItem(storageKey);
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", theme === "dark" ? "#071a16" : "#173f35");
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(preferredTheme);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(storageKey, theme);
  }, [theme]);

  return {
    theme,
    toggleTheme: () =>
      setTheme((current) => (current === "dark" ? "light" : "dark")),
  };
}
