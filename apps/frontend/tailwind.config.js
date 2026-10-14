/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Montserrat", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "0.5rem",
        base: "0.75rem",
        lg: "1rem",
      },
      boxShadow: {
        subtle: "0 1px 2px rgba(24, 24, 27, 0.05)",
        card: "0 10px 30px -15px rgba(24, 24, 27, 0.10)",
        "card-hover": "0 16px 36px -18px rgba(24, 24, 27, 0.15)",
        float: "0 20px 48px -20px rgba(24, 24, 27, 0.20)",
      },
      colors: {
        brand: {
          ink: "#18181B",
          "ink-elevated": "#27272A",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          soft: "#FAFAFA",
          muted: "#F4F4F5",
        },
        border: {
          DEFAULT: "#E4E4E7",
          strong: "#A1A1AA",
        },
        primary: "#18181B",
        secondary: "#52525B",
        muted: "#71717A",
        text: {
          primary: "#18181B",
          secondary: "#52525B",
          muted: "#71717A",
        },
        success: {
          DEFAULT: "#15803D",
          soft: "#F0FDF4",
        },
        warning: {
          DEFAULT: "#B45309",
          soft: "#FEF3C7",
        },
        info: {
          DEFAULT: "#475569",
          soft: "#F1F5F9",
        },
        danger: {
          DEFAULT: "#B91C1C",
          soft: "#FEF2F2",
        },
      },
    },
  },
  plugins: [],
}
