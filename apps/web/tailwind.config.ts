import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        app: "#050608",
        surface: "#07090C",
        card: "#0C0E12",
        primary: "#ECEEF2",
        secondary: "#949BA6",
        muted: "#565E68",
        accent: {
          blue: "#4A7BA7",
          cyan: "#7EB8D8",
          "cyan-soft": "#6AA3C4",
        },
        status: {
          success: "#22C55E",
          warning: "#C9A227",
          error: "#CF5C5C",
        },
      },
      borderRadius: {
        card: "28px",
        shell: "30px",
        well: "22px",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        raised:
          "0 24px 48px rgba(0,0,0,0.45), 0 48px 88px rgba(0,0,0,0.38), 0 12px 40px rgba(100,165,210,0.11)",
      },
    },
  },
  plugins: [],
};

export default config;
