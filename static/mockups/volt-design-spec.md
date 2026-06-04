# Volt Design System — CityLab

## Design Philosophy

**Swiss precision meets premium SaaS.** Light canvas, violet accent, monospace data. The dashboard communicates authority through restraint — generous whitespace, a strict type hierarchy, and a single accent colour that draws attention exactly where it matters: the data.

The light background is a deliberate counterpoint to the dark-mode default of every other energy dashboard. It signals confidence and clarity. Data is presented with editorial precision — like a Bloomberg terminal redesigned by the Linear team.

**Core principles:**
1. **Data first** — every visual decision serves legibility. Decorative elements earn their place or get removed
2. **One accent** — violet (#7C3AED) is the only brand colour. Everything else is neutral. This creates instant recognition
3. **Monospace for numbers** — JetBrains Mono for all numerical data. Tabular alignment, technical credibility
4. **Proportional for prose** — Inter for labels, navigation, and body text. Clean, invisible, professional
5. **Whitespace is structure** — spacing communicates hierarchy as much as size and weight do

---

## Colour Tokens

### Core Palette

```css
:root {
  /* Backgrounds */
  --bg:             #fafafa;    /* page background */
  --bg-card:        #ffffff;    /* card / elevated surface */
  --bg-surface:     #f4f4f5;   /* inset surface, input backgrounds, weather cards */

  /* Borders */
  --border:         #e4e4e7;    /* default card/section border */
  --border-strong:  #d4d4d8;    /* emphasized borders, active states */

  /* Brand — Violet */
  --violet:         #7c3aed;    /* primary accent — brand, live badge, active states */
  --violet-light:   #ede9fe;    /* light violet wash — selected tabs, hover backgrounds */
  --violet-mid:     #c4b5fd;    /* medium violet — price hero border, chart elements */
  --violet-bg:      rgba(124, 58, 237, 0.06);  /* barely-there violet tint — hero gradient, summary bars */

  /* Text */
  --text-primary:   #09090b;    /* headings, price values, primary content */
  --text-secondary: #52525b;    /* body text, labels, descriptions */
  --text-tertiary:  #a1a1aa;    /* metadata, units, timestamps, card labels */
}
```

### Semantic Colours — Status

```css
:root {
  /* Success / Normal / Low price */
  --green:          #16a34a;
  --green-bg:       #f0fdf4;

  /* Error / Constrained / High price */
  --red:            #dc2626;
  --red-bg:         #fef2f2;

  /* Warning / Caution / Amber price */
  --amber:          #d97706;
  --amber-bg:       #fffbeb;

  /* Teal — wind, hydro, renewable positive */
  --teal:           #0d9488;
  --teal-bg:        #f0fdfa;

  /* Spike — extreme price event */
  --spike:          #dc2626;
  --spike-bg:       #fef2f2;
}
```

### Generation Mix Colours

These are fixed per fuel type — used in charts, dots, and bars:

| Fuel Type | Hex | Usage |
|-----------|-----|-------|
| Brown Coal | `#6366f1` | Indigo — dominant baseload |
| Wind | `#0ea5e9` | Sky blue — renewable primary |
| Solar | `#eab308` | Yellow — solar energy |
| Gas | `#a855f7` | Purple — peaking gas |
| Hydro | `#14b8a6` | Teal — hydro storage |
| Battery | `#f472b6` | Pink — battery dispatch |
| Black Coal | `#64748b` | Slate — if present |
| Other | `#94a3b8` | Light slate — catch-all |

### Price State Mapping

| State | Text Colour | Badge BG | Trigger |
|-------|------------|----------|---------|
| Low | `--green` | `--green-bg` | < $50/MWh |
| Normal | `--text-primary` | none | $50–$100 |
| Amber | `--amber` | `--amber-bg` | $100–$300 |
| High | `--red` | `--red-bg` | $300–$5,000 |
| Spike | `--red` | `--red-bg` | > $5,000 (with flash animation) |

---

## Typography

### Font Stack

```css
/* UI text — labels, navigation, body */
font-family: 'Inter', system-ui, -apple-system, sans-serif;

/* Data — prices, MW values, timestamps, chart labels */
font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
```

Load via Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### Type Scale

| Role | Font | Size | Weight | Colour | Letter-spacing | Example |
|------|------|------|--------|--------|---------------|---------|
| Price hero | JetBrains Mono | 56px (mobile) / 72px (desktop) | 600 | `--text-primary` | -0.04em | `$87.42` |
| Price unit | JetBrains Mono | 20px / 24px | 400 | `--text-tertiary` | — | `.42` |
| Metric large | JetBrains Mono | 18px / 22px | 600 | `--text-primary` | — | `5,842 MW` |
| Metric medium | JetBrains Mono | 13px / 14px | 500 | `--text-primary` | — | `+220 MW` |
| Page title | Inter | 20px / 24px | 700 | `--text-primary` | -0.03em | `CityLab` |
| Card label | Inter | 11px | 600 | `--text-tertiary` | 0.04em, uppercase | `SPOT PRICE` |
| Body | Inter | 13px / 14px | 400–500 | `--text-secondary` | — | `Brown Coal` |
| Caption | Inter | 10px–11px | 500 | `--text-tertiary` | 0.05em, uppercase | `PRE-DISPATCH` |
| Nav item | Inter | 14px | 500 | `--text-secondary` | — | `Energy` |
| Badge | Inter | 10px–11px | 600 | varies | 0.03em, uppercase | `STRONG` |

### Rules

- ALL numerical data uses JetBrains Mono — prices, MW, percentages, temperatures, timestamps
- ALL labels, navigation, and prose use Inter
- Section headers are uppercase, tracked, 11px, `--text-tertiary` — they whisper, they don't shout
- The price hero is the only element above 24px on mobile. It owns the top of the visual hierarchy

---

## Spacing System

Base unit: **4px**. All spacing is a multiple of 4.

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight gaps (icon to label) |
| `space-2` | 8px | Intra-component (gap between gen rows, ic rows) |
| `space-3` | 12px | Card label to content, inter-card gap (mobile) |
| `space-4` | 16px | Card padding (compact), section separators |
| `space-5` | 20px | Page horizontal padding (mobile), card padding (standard) |
| `space-6` | 24px | Card padding (spacious), hero vertical padding |
| `space-8` | 32px | Desktop page padding |
| `space-10` | 40px | Bottom padding (scroll clearance) |

### Card Dimensions

| Property | Value |
|----------|-------|
| Padding | 18px (mobile) / 24px (desktop) |
| Border radius | 12px |
| Border | 1px solid `--border` |
| Background | `--bg-card` (white) |
| Gap between cards | 10px (mobile) / 16px (desktop) |

---

## Responsive Layout

### Breakpoints

| Name | Width | Target |
|------|-------|--------|
| Mobile | < 768px | iPhone (all sizes) |
| Tablet | 768px–1023px | iPad portrait |
| Desktop | 1024px–1279px | iPad landscape, small laptops |
| Wide | 1280px+ | Mac, large screens |

### Layout Grid by Breakpoint

**Mobile (< 768px):**
- Single column, full-width cards
- Horizontal padding: 20px
- No sidebar — use sticky top header with hamburger or bottom tab bar
- Cards stack vertically with 10px gap

**Tablet (768px–1023px):**
- 2-column grid for dashboard panels
- Price hero: full-width (spans both columns)
- Forecast: full-width
- Generation + Interconnectors: side by side
- Weather: full-width (4-column sub-grid maintained)
- Sources: full-width
- Collapsible sidebar or slide-out nav

**Desktop (1024px+):**
- Fixed sidebar (240px width) + content area
- Content: 2-column grid, max-width 1200px, centered
- Price hero: full-width span
- Forecast: full-width span
- Generation + Interconnectors: 2 columns
- Weather + Sources: full-width span

### Sidebar (Tablet + Desktop)

| Property | Value |
|----------|-------|
| Width | 240px (desktop) / slide-out (tablet) / hidden (mobile) |
| Background | `--bg-card` |
| Border right | 1px solid `--border` |
| Logo area padding | 20px |
| Nav item height | 40px |
| Nav item padding | 12px 16px |
| Nav item radius | 8px |
| Active nav | `--violet-light` background, `--violet` text |
| Hover nav | `--bg-surface` background |

### Mobile Header

| Property | Value |
|----------|-------|
| Height | 56px |
| Background | `--bg-card` |
| Border bottom | 1px solid `--border` |
| Logo + brand left-aligned | 30px mark + "CityLab" |
| Live badge right-aligned | Violet pill |
| Sticky | `position: sticky; top: 0; z-index: 50` |

---

## Component Specifications

### Price Hero Card

The visual anchor of the dashboard. Elevated treatment — violet border, gradient wash.

| Property | Value |
|----------|-------|
| Border | 2px solid `--violet-mid` |
| Background | `linear-gradient(180deg, var(--violet-bg) 0%, var(--bg-card) 100%)` |
| Text align | Center |
| Padding | 24px 18px 20px (mobile) / 32px 24px (desktop) |

**Internal layout:**
1. Card label: "SPOT PRICE · $/MWh"
2. Price value: 56px mono, `--text-primary` (dynamic colour based on price state)
3. Trend pill: rounded-full, `--green-bg` / `--green` (or red for falling)
4. Separator: 1px `--border`, 16px margin-top/padding-top
5. Meta row: 3-column grid (Demand, Forecast, 24h Range)

### Forecast Chart Card

| Property | Value |
|----------|-------|
| Chart background | `--bg-surface` with 1px `--border`, 8px radius |
| Forecast line | 2px, `--violet` |
| Forecast fill | `rgba(124, 58, 237, 0.12)` gradient to transparent |
| Actual line | 1.5px, `--text-tertiary`, dashed (4,3) |
| Now marker | 1px dashed `--violet-mid` vertical line |
| Y-axis | Price, `$` prefix formatter |
| Grid lines | 1px `--border` |
| Tick labels | JetBrains Mono, 10px, `--text-tertiary` |

### Generation Mix Card

Horizontal bar layout (not doughnut). Each fuel type as a row:

| Element | Spec |
|---------|------|
| Fuel dot | 10px square, 3px radius, fuel colour |
| Label | Inter 13px, `--text-secondary` |
| Bar container | 100px wide (mobile) / flex-grow (desktop), 6px height, `--bg-surface`, 3px radius |
| Bar fill | fuel colour, width proportional to output |
| Value | JetBrains Mono 12px, 500 weight, right-aligned |
| Total row | border-top separator, "Total output" label + bold value |

### Interconnectors Card

| Element | Spec |
|---------|------|
| Summary bar | `--violet-bg` background, 8px radius, flex between label and net value |
| Net value | JetBrains Mono 600, `--violet` |
| Row separator | 1px `--bg-surface` bottom border |
| Status dot | 7px circle — green (normal), amber (high), red (constrained) |
| Name | Inter 13px, 500 weight |
| Partner region | Inter 11px, `--text-tertiary` |
| Direction | Inter 10px, `--text-tertiary` |
| Flow value | JetBrains Mono 12px, 500 weight |

### Weather / Renewable Outlook Card

2x2 grid of sub-cards:

| Element | Spec |
|---------|------|
| Sub-card | `--bg-surface` background, 1px `--border`, 10px radius, 14px padding |
| Label | 10px uppercase, `--text-tertiary` |
| Value | JetBrains Mono 22px, 600 weight |
| Unit | 12px, `--text-tertiary` |
| Band badge | 10px uppercase, 600 weight, 4px radius, semantic colour bg/text |

**Band colour mapping:**

| Band | Background | Text |
|------|-----------|------|
| Wind Strong | `--teal-bg` | `--teal` |
| Wind Moderate | lighter teal | `--teal` |
| Wind Light | `--bg-surface` | `--text-tertiary` |
| Solar Sunny | `--amber-bg` | `--amber` |
| Solar Partly Cloudy | lighter amber | `--amber` |
| Solar Overcast | `--bg-surface` | `--text-tertiary` |
| Rain Heavy | `#eff6ff` | `#2563eb` |
| Rain Moderate | `#eff6ff` | `#3b82f6` |
| Rain Light | `#f0f9ff` | `#60a5fa` |
| Rain Dry | `--bg-surface` | `--text-tertiary` |

### Source Health Bar

Compact footer element:

| Element | Spec |
|---------|------|
| Layout | flex, space-around |
| Card padding | 12px 18px |
| Source dot | 6px circle — green (ok) / amber (stale) / red (error) |
| Label | Inter 11px, 500 weight, `--text-secondary` |

### Live Badge

| Property | Value |
|----------|-------|
| Background | `--violet-bg` |
| Text | `--violet`, 11px, 600 weight |
| Padding | 4px 10px |
| Radius | 20px (pill) |
| Dot | 6px circle, `--violet`, pulsing animation (2s ease-in-out, opacity 1→0.3) |

### Region Pill

| Property | Value |
|----------|-------|
| Background | `--bg-surface` |
| Border | 1px `--border` |
| Text | 12px, 600 weight, `--text-primary` |
| Padding | 5px 12px |
| Radius | 20px |

### Buttons

| Variant | Background | Text | Border | Hover |
|---------|-----------|------|--------|-------|
| Primary | `--violet` | white | none | `#6d28d9` (darker violet) |
| Secondary | `--bg-card` | `--text-secondary` | 1px `--border` | `--bg-surface` |
| Ghost | transparent | `--violet` | none | `--violet-bg` |

All buttons: Inter 13px, 500 weight, 8px radius, 8px 16px padding.

### Trend Pill

| Direction | Background | Text | Icon |
|-----------|-----------|------|------|
| Rising | `--green-bg` | `--green` | ↑ |
| Falling | `--red-bg` | `--red` | ↓ |
| Flat | `--bg-surface` | `--text-tertiary` | → |

Pill: 12px, 600 weight, 20px radius, 3px 10px padding.

---

## Animation & Transitions

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Live dot pulse | opacity 1 → 0.3 → 1 | 2s | ease-in-out, infinite |
| Price spike flash | opacity 1 → 0.5 → 1 | 1s | linear, infinite (only during spike state) |
| Hover transitions | background-color, border-color | 150ms | ease |
| Chart data update | dataset transition | 300ms | — (Chart.js default) |
| Card hover (desktop) | border-color to `--border-strong` | 150ms | ease |
| HTMX swap | opacity fade-in | 200ms | ease-out |

### Price Spike Animation

```css
@keyframes spike-flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.price-spike .price-value {
  color: var(--red);
  animation: spike-flash 1s linear infinite;
}
```

---

## Login Page

Centered card on `--bg` background. No sidebar.

| Element | Spec |
|---------|------|
| Card | max-width 400px, `--bg-card`, 12px radius, 1px `--border`, 32px padding |
| Logo | Violet brand mark (30px) + "CityLab" text, centered |
| Subtitle | "Victorian Energy Market", Inter 13px, `--text-tertiary`, centered |
| Input fields | `--bg-surface` background, 1px `--border`, 8px radius, 12px padding |
| Input focus | 2px ring `--violet-mid`, border `--violet` |
| Submit button | Full-width primary button |
| Error message | `--red` text, `--red-bg` background, 8px radius, 12px padding |

---

## Error Pages (404, 500)

Centered on `--bg`, no sidebar.

| Element | Spec |
|---------|------|
| Error code | JetBrains Mono 72px, 600 weight, `--text-tertiary` |
| Message | Inter 16px, `--text-secondary` |
| Home link | Ghost button style |

---

## Chart.js Theme Config

```javascript
const voltChartDefaults = {
  color: '#a1a1aa',                    // tick label colour
  borderColor: '#e4e4e7',             // grid line colour
  font: { family: "'JetBrains Mono', monospace", size: 10 },
  plugins: {
    legend: { display: false },        // custom legends only
    tooltip: {
      backgroundColor: '#09090b',
      titleColor: '#e4e4e7',
      bodyColor: '#e4e4e7',
      bodyFont: { family: "'JetBrains Mono', monospace" },
      borderColor: '#27272a',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 10,
    }
  },
  scales: {
    x: { grid: { display: false }, ticks: { color: '#a1a1aa', maxTicksLimit: 8 } },
    y: { grid: { color: '#e4e4e7' }, ticks: { color: '#a1a1aa' } }
  }
};
```

---

## Tailwind Config Mapping

The Volt palette maps to Tailwind's zinc scale for neutrals, with a custom `volt` key for the violet accent:

```javascript
// tailwind.config.js
module.exports = {
  content: ['./templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        volt: {
          50:  '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',   // primary
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
```

Neutral scale: use Tailwind's built-in `zinc` (`zinc-50` through `zinc-950`) — it matches the Volt neutral palette exactly.

---

## Accessibility

- All text passes WCAG AA contrast on white backgrounds (Inter 13px+ at `--text-secondary` = 7.1:1 ratio)
- Violet accent on white: 4.6:1 — passes AA for large text, borderline for small. Use only for interactive elements (badges, buttons), not body text
- Status colours (green, red, amber) are never the sole indicator — always paired with text labels or icons
- Focus rings: 2px `--violet-mid` outline with 2px offset on all interactive elements
- Reduced motion: respect `prefers-reduced-motion` — disable pulse, spike flash, and chart animations
