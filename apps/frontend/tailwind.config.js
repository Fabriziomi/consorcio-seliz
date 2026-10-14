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
        subtle: "0 1px 2px rgba(38, 48, 60, 0.06)",
        card: "0 12px 32px -20px rgba(38, 48, 60, 0.22)",
        "card-hover": "0 18px 40px -22px rgba(38, 48, 60, 0.28)",
        float: "0 24px 56px -24px rgba(38, 48, 60, 0.34)",
      },
      colors: {
        brand: {
          ink: "#1B1B1D",
          "ink-elevated": "#303034",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          soft: "#F8F9FA",
          muted: "#F1F3F5",
        },
        border: {
          DEFAULT: "#E5E7EB",
          strong: "#62656B",
        },
        primary: "#1B1B1D",
        secondary: "#62656B",
        muted: "#62656B",
        text: {
          primary: "#1B1B1D",
          secondary: "#62656B",
          muted: "#62656B",
        },
        success: {
          DEFAULT: "#2F6F5E",
          soft: "#EAF4F0",
        },
        warning: {
          DEFAULT: "#8A5A00",
          soft: "#FBF3E4",
        },
        info: {
          DEFAULT: "#3A6576",
          soft: "#EAF2F5",
        },
        danger: {
          DEFAULT: "#A33D47",
          soft: "#FBECEE",
        },
      },
    },
  },
  plugins: [],
}
