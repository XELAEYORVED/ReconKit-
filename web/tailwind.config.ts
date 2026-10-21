import type { Config } from "tailwindcss";

/**
 * ReconKit design direction — "Apple".
 * Bright, airy light UI in Apple's palette: #f5f5f7 canvas, white cards with
 * soft shadows and large radii, system-blue accent, SF (system) typography,
 * hairline #d2d2d7 dividers, and iOS system colors for the risk ramp.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#f5f5f7", // Apple canvas grey
        panel: "#ffffff", // card surface
        panel2: "#f5f5f7", // inset / raised-grey surface
        border: "#d2d2d7", // Apple hairline
        ink: "#1d1d1f", // Apple near-black text
        muted: "#6e6e73", // Apple secondary grey
        accent: "#0071e3", // Apple system blue (primary)
        accent2: "#0066cc", // deeper blue (links, data labels)
        risk: {
          low: "#34c759", // iOS green
          medium: "#ff9f0a", // iOS amber
          high: "#ff9500", // iOS orange
          critical: "#ff3b30", // iOS red
        },
      },
      fontFamily: {
        // System San Francisco on Apple devices; clean native fallbacks elsewhere.
        display: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Display"',
          '"Segoe UI"',
          "system-ui",
          "sans-serif",
        ],
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Text"',
          '"Segoe UI"',
          "system-ui",
          "sans-serif",
        ],
        mono: ['ui-monospace', '"SF Mono"', "Menlo", "Monaco", "monospace"],
      },
      borderRadius: {
        xl: "14px",
        "2xl": "18px",
        "3xl": "24px",
      },
      boxShadow: {
        // Apple-style soft, diffuse elevation.
        soft: "0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -12px rgba(0,0,0,0.12)",
        card: "0 2px 10px rgba(0,0,0,0.06)",
        accent: "0 4px 14px -4px rgba(0,113,227,0.45)",
      },
      backdropBlur: {
        apple: "20px",
      },
    },
  },
  plugins: [],
} satisfies Config;
