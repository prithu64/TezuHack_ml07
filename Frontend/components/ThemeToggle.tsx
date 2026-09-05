"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(
      "student-support-theme",
    ) as Theme | null;
    const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)")
      .matches
      ? "dark"
      : "light";
    const nextTheme = savedTheme ?? preferredTheme;
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
  }, []);

  function toggleTheme() {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    window.localStorage.setItem("student-support-theme", nextTheme);
  }

  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
    >
      <span className="theme-icon" aria-hidden="true">
        {theme === "light" ? "☾" : "☀"}
      </span>
      <span>{theme === "light" ? "Dark" : "Light"}</span>
    </button>
  );
}
