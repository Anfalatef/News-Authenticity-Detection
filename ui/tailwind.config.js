/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#F5E9FA",
          100: "#E9D3F5",
          200: "#D4A8EB",
          300: "#B67EDD",
          400: "#9552C9",
          500: "#6A2BA7",
          600: "#542086",
          700: "#401965",
          800: "#2E1247",
          900: "#1F0C30",
        },
        accent: {
          50: "#FCE7F3",
          100: "#FBCFE8",
          200: "#F9A8D4",
          300: "#F472B6",
          400: "#EC4899",
          500: "#DB2777",
          600: "#BE185D",
          700: "#9D174D",
          800: "#831843",
          900: "#701A3B",
        },
        success: {
          bg: "#ECFDF5",
          text: "#0F766E",
          border: "#99F6E4",
        },
        warning: {
          bg: "#FFF7ED",
          text: "#C2410C",
          border: "#FED7AA",
        },
        error: {
          bg: "#FEF2F2",
          text: "#B91C1C",
          border: "#FECACA",
        },
        ink: "#1B1023",
        muted: "#756B82",
        surface: "#FFFFFF",
        canvas: "#FBF7FD",
        line: "#E8DEEF",
        telemetry: {
          bg: "#F3EAF7",
          text: "#5E526B",
          border: "#E4D6EE",
        },
      },
      boxShadow: {
        soft: "0 24px 60px rgba(25, 12, 35, 0.16)",
      },
    },
  },
  plugins: [],
};
