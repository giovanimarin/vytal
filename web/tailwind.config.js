/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:      '#0f172a',
        surface: '#1e293b',
        border:  '#334155',
        muted:   '#64748b',
        text:    '#f8fafc',
        sub:     '#94a3b8',
        brand:   '#3b82f6',
        green:   '#4CAF50',
        yellow:  '#FFC107',
        red:     '#F44336',
      },
    },
  },
  plugins: [],
}
