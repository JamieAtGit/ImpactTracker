/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'green': {
          700: '#15803d', // Adjust this to match your design
        },
      },
    },
  },
  plugins: [],
}