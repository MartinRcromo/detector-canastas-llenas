/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primarios
        'blue-industrial': '#1E3A5F',
        'gray-graphite': '#2D3748',

        // Secundarios
        'orange-mechanic': '#F56B2A',
        'green-progress': '#10B981',
        'yellow-alert': '#F59E0B',

        // Neutros
        'gray-light': '#F7FAFC',
        'gray-medium': '#E2E8F0',
        'gray-text': '#4A5568',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 4px 16px rgba(0, 0, 0, 0.12)',
      },
    },
  },
  plugins: [],
}
