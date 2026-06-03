/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./src/**/*.py",
  ],
  // Energy dashboard component classes are built from dynamic Jinja values
  // (e.g. chip-wind-{{ band }}, price-{{ state }}), so Tailwind's content
  // scanner can't see them — safelist them explicitly.
  safelist: [
    'price-low', 'price-amber', 'price-high', 'price-spike', 'price-unknown',
    'ic-normal', 'ic-high', 'ic-constrained', 'ic-na',
    'source-ok', 'source-bad',
    'chip-wind-strong', 'chip-wind-moderate', 'chip-wind-light', 'chip-wind-unknown',
    'chip-solar-sunny', 'chip-solar-partly-cloudy', 'chip-solar-overcast', 'chip-solar-unknown',
    'chip-rain-dry', 'chip-rain-light', 'chip-rain-moderate', 'chip-rain-heavy', 'chip-rain-unknown',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        citylab: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
      },
    },
  },
  plugins: [],
}
