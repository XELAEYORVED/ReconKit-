import type { Config } from "tailwindcss";

/**
 * ReconKit design direction — "steel".
 * Cool graphite surfaces, a steel-blue signal accent (brand/primary), a paler
 * ice-blue counter-accent, and a warm earth-toned risk ramp so status pops
 * against the cool UI and reads as data, never as brand.
 * Type system: IBM Plex superfamily (engineered, deliberate — not the
 * ubiquitous Inter/trendy-serif defaults).
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        base: "#10151a", // cool graphite-black
        panel: "#171d23", // surface
        panel2: "#202830", // raised surface
        border: "#2d363f", // cool hairline
        ink: "#dbe3ea", // cool light text
        muted: "#8794a1", // cool grey
        accent: "#5a8cb3", // steel blue (brand, primary)
        accent2: "#9bbdd6", // pale ice-blue (links, data labels)
        risk: {
          low: "#7fa07a", // sage
          medium: "#cf9a46", // amber
          high: "#c56b3c", // clay
          critical: "#b2453a", // brick
        },
      },
      fontFamily: {
        display: ['"IBM Plex Sans Condensed"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"IBM Plex Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        accent: "0 0 0 1px rgba(90,140,179,0.30), 0 6px 20px -8px rgba(90,140,179,0.50)",
        soft: "0 1px 0 rgba(255,255,255,0.03) inset, 0 10px 30px -18px rgba(0,0,0,0.8)",
      },
    },
  },
  plugins: [],
} satisfies Config;
