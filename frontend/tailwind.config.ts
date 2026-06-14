import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a0c",
        surface: "#141418",
        border: "#26262c",
        accent: "#0a84ff",
        success: "#30d158",
        warning: "#e0a106",
        danger: "#ff453a",
        muted: "#86868b",
        fg: "#f5f5f7",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
