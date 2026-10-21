import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        base: "#0a0a0f",
        panel: "#0f1117",
        panel2: "#141821",
        border: "#1f2937",
        neon: "#39ff14",
        cyan: "#22d3ee",
        risk: {
          low: "#22c55e",
          medium: "#eab308",
          high: "#f97316",
          critical: "#ef4444",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        neon: "0 0 12px rgba(57,255,20,0.35)",
      },
    },
  },
  plugins: [],
} satisfies Config;
