/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        panel: "#0f172a",
        border: "#1f2a44",
        accent: "#22d3ee",
        muted: "#94a3b8"
      },
      boxShadow: {
        glow: "0 0 24px rgba(34,211,238,0.18)"
      }
    }
  },
  plugins: []
};
