/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#07111F",
        surface: "#101F33",
        primary: "#22D3EE",
        ai: "#8B5CF6",
        success: "#34D399",
        warning: "#FBBF24",
        danger: "#FB7185",
      },
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};