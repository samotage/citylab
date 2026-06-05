/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./src/**/*.py",
  ],
  safelist: [
    'price-low', 'price-amber', 'price-high', 'price-spike', 'price-unknown',
    'ic-normal', 'ic-high', 'ic-constrained', 'ic-na',
    'source-ok', 'source-bad', 'source-stale',
    'chip-wind-strong', 'chip-wind-moderate', 'chip-wind-light', 'chip-wind-unknown',
    'chip-solar-sunny', 'chip-solar-partly-cloudy', 'chip-solar-overcast', 'chip-solar-unknown',
    'chip-rain-dry', 'chip-rain-light', 'chip-rain-moderate', 'chip-rain-heavy', 'chip-rain-unknown',
    'sc-type-active', 'sc-impact-up', 'sc-impact-down',
    'inertia-state-comfortable', 'inertia-state-watch', 'inertia-state-brittle',
    'inertia-gauge-comfortable', 'inertia-gauge-watch', 'inertia-gauge-brittle',
  ],
  theme: {
    extend: {
      colors: {
        volt: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
