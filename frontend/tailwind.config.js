/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mac-bg': '#1e1e1e',
        'mac-sidebar': '#252526',
        'mac-accent': '#007acc',
        'mac-text': '#cccccc',
        'mac-text-secondary': '#858585',
        'mac-border': '#3c3c3c',
        'mac-hover': '#2a2d2e',
      },
      fontFamily: {
        'sans': ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
