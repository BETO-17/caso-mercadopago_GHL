/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-main': '#2E2E34',
        'bg-sidebar': '#393A41',
        'text-primary': '#FFFFFF',
      },
      backgroundImage: {
        'gradient-button': 'linear-gradient(to right, #0BA9D9, #1190DD, #2074E6)',
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

