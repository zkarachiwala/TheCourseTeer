"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const THEMES = ["system", "light", "dark"] as const;
const LABELS: Record<string, string> = { system: "System", light: "Light", dark: "Dark" };

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  const next = THEMES[(THEMES.indexOf(theme as (typeof THEMES)[number]) + 1) % THEMES.length];

  return (
    <button
      onClick={() => setTheme(next)}
      className="rounded border border-gray-300 px-3 py-1 text-sm dark:border-gray-600"
    >
      {LABELS[theme ?? "system"]}
    </button>
  );
}
