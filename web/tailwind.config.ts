import type { Config } from "tailwindcss";

/**
 * ReconKit design direction — "dossier".
 * Warm espresso surfaces (not cold black), a brass signal accent, a cool
 * slate-blue counter-accent for temperature contrast, and an earth-toned
 * risk ramp so status reads as data, never as brand.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        base: "#141210", // warm espresso-black
        panel: "#1c1915", // surface
        panel2: "#262019", // raised surface
        border: "#3a3125", // warm hairline
        ink: "#ece2d2", // warm parchment text
        muted: "#9a8f7c", // warm grey
        accent: "#e3a53b", // brass / signal (brand, primary)
        accent2: "#8aa7bd", // cool slate-blue (links, data labels)
        risk: {
          low: "#8fa06a", // sage
          medium: "#c9972f", // ochre
          high: "#c2622c", // burnt orange
          critical: "#a93a30", // brick
        },
      },
      fontFamily: {
        display: ['"Fraunces"', "ui-serif", "Georgia", "serif"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        accent: "0 0 0 1px rgba(227,165,59,0.25), 0 6px 20px -8px rgba(227,165,59,0.45)",
        soft: "0 1px 0 rgba(255,255,255,0.03) inset, 0 10px 30px -18px rgba(0,0,0,0.8)",
      },
      backgroundImage: {
        grain:
          "radial-gradient(circle at 1px 1px, rgba(236,226,210,0.035) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
} satisfies Config;
