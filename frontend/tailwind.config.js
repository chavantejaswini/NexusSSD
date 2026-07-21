/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: "#0b1220",
          panel: "#141d2e",
          accent: "#3b82f6",
        },
      },
    },
  },
  plugins: [],
};
