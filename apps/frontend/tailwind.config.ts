import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Montserrat", "sans-serif"],
      },
      colors: {
        // Paleta Sobria y Monocromática (Slate / Charcoal)
        surface: {
          DEFAULT: "#0F172A",
          muted: "#1E293B",
          card: "#111827",
          border: "#334155",
        },
        monochrome: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
          950: "#020617",
        },
        // Acentos de estado aislados y desaturados
        status: {
          emergency: "#991B1B", // Rojo sobrio
          pending: "#854D0E",   // Ámbar apagado
          resolved: "#166534",  // Verde bosque profundo
        }
      },
    },
  },
  plugins: [],
};

export default config;
