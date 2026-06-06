# citEther Brand Guidelines

## Brand Identity

**citEther** — a portmanteau of *city* and *ether*. The city is the physical infrastructure: buildings, transmission lines, substations, load centres. The ether is the invisible intelligence that connects, balances, and optimises the grid for better outcomes. citEther sits at the intersection — where physical energy infrastructure meets AI-driven decision-making.

### Brand Positioning

citEther is an energy intelligence platform for the Victorian electricity grid. It ingests real-time market data, weather conditions, solar forecasts, and generation mix to surface actionable intelligence about grid state, price dynamics, and demand-supply balance.

The brand communicates: **precision, convergence, and intelligent balance.**

---

## The Mark

The citEther mark is a **tilted hash** — two amber diagonal bars intersecting two charcoal horizontal bars. The hash symbol inherently reads as "network" and "grid." The tilt adds energy and forward momentum. The amber-through-charcoal weave represents competing forces (generation vs load, supply vs demand) meeting at a managed equilibrium.

### Logo Files

| File | Use |
|------|-----|
| `citether-mark.svg` | Production vector — fixed 1024×1024 |
| `citether-mark-responsive.svg` | Scalable vector — no fixed dimensions, scales to container |
| `citether-mark-1024.png` | Print, high-res display |
| `citether-mark-512.png` | Hero images, large display |
| `citether-mark-256.png` | Social media, thumbnails |
| `citether-mark-128.png` | App icons |
| `citether-mark-64.png` | Navigation, toolbar |
| `citether-mark-32.png` | Favicon 2× |
| `citether-mark-16.png` | Favicon |

### Clear Space

Maintain a clear zone around the mark equal to the width of one bar in the hash. No text, imagery, or other graphic elements should intrude into this zone.

### Minimum Size

The mark remains legible down to **32×32 pixels**. Do not reproduce smaller than this.

### Orientation

The mark is always presented at its designed tilt angle. Do not rotate, skew, or straighten it.

---

## Colour Palette

### Primary Colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Amber** | `#E8A838` | 232, 168, 56 | Primary accent. The diagonal bars in the mark. Represents energy, warmth, the city's active pulse. Use for primary CTAs, highlights, key data points. |
| **Charcoal** | `#2D2926` | 45, 41, 38 | Primary dark. The horizontal bars in the mark. Represents infrastructure, stability, the physical grid. Use for body text, dark backgrounds, headers. |

### Secondary Colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Deep Teal** | `#0D7377` | 13, 115, 119 | The ether — intelligence, data, communication. Use for secondary accents, interactive elements, data visualisation highlights. |
| **White** | `#FFFFFF` | 255, 255, 255 | Backgrounds, clear space, breathing room. |
| **Warm Grey** | `#8A8480` | 138, 132, 128 | Secondary text, metadata, borders, disabled states. |

### Extended Palette (Data Visualisation)

| Name | Hex | Usage |
|------|-----|-------|
| **Amber Light** | `#F5D08A` | Chart fills, light accents, hover states |
| **Teal Light** | `#4DA8AB` | Secondary data series, positive indicators |
| **Teal Dark** | `#094F52` | Dark mode accents, deep chart backgrounds |
| **Charcoal Light** | `#4A4542` | Subtle borders, card backgrounds on dark |
| **Signal Red** | `#D94F4F` | Alerts, negative price events, critical states |
| **Signal Green** | `#4CAF50` | Positive states, healthy indicators |

### Colour Usage Rules

- The amber and charcoal pairing from the mark is the primary brand expression. When only two colours are available, use these.
- Deep teal is the digital accent — it does not appear in the mark itself but complements it on screen.
- Never use amber on teal directly — the contrast is insufficient for text. Amber on charcoal or white; teal on charcoal or white.
- Signal colours (red, green) are reserved for data states. They are not brand colours and should not be used decoratively.

---

## Typography

### Primary Typeface

**Inter** — a clean, modern sans-serif optimised for screen readability. Used across the dashboard UI and all digital touchpoints.

| Weight | Usage |
|--------|-------|
| Inter 700 (Bold) | Page titles, hero numbers, key metrics |
| Inter 600 (SemiBold) | Section headings, card titles, navigation |
| Inter 400 (Regular) | Body text, descriptions, labels |
| Inter 300 (Light) | Metadata, timestamps, secondary information |

### Monospace

**JetBrains Mono** or **SF Mono** — for data values, code references, API responses, and tabular numeric data on the dashboard.

### The citEther Wordmark

When the name appears as text, it is always styled as **citEther** — lowercase "cit", uppercase "E", lowercase "ther". In branded contexts where colour is available:

- **cit** in Amber (`#E8A838`)
- **Ether** in Deep Teal (`#0D7377`)

In monochrome contexts, the full word appears in Charcoal on light backgrounds or White on dark backgrounds. The casing distinction (citEther) is maintained in all contexts.

### Typography Rules

- Minimum body text size: 14px on screen, 10pt in print.
- Line height for body text: 1.5× the font size.
- Maximum line length: 72 characters for comfortable reading.
- Numbers on the dashboard should use tabular (monospace) figures so columns align.

---

## Brand in Context

### Dashboard UI

The dashboard uses a dark theme grounded in Charcoal with Amber and Teal as the primary data colours. White is used for card surfaces. The mark appears in the navigation header at 32×32 or 48×48.

### On Dark Backgrounds

Use the mark as-is — the amber and charcoal bars read well against dark backgrounds (#1a1a1a to #2D2926 range). If contrast is insufficient on very dark charcoal backgrounds, the charcoal bars may be lightened to `#4A4542`.

### On Light Backgrounds

The mark renders at full contrast on white or light grey backgrounds. This is the preferred presentation.

### On Coloured Backgrounds

Avoid placing the mark on amber or teal backgrounds — the bars lose contrast. If unavoidable, use the monochrome mark variant (all charcoal or all white).

---

## Do and Don't

### Do

- Use the mark at its designed tilt angle
- Maintain clear space around the mark
- Use the responsive SVG for web contexts
- Pair amber with charcoal or white for text
- Write the name as "citEther" with consistent casing

### Don't

- Rotate, stretch, or distort the mark
- Place the mark on amber or teal backgrounds
- Use the mark smaller than 32×32 pixels
- Add drop shadows, outlines, or effects to the mark
- Rearrange the colour assignment of the bars (amber is always the diagonals, charcoal is always the horizontals)
- Write the name as "Citether", "CitEther", "CITETHER", or "citether"

---

## File Naming Convention

All brand assets follow the pattern:

```
citether-mark-{variant}-{size}.{format}
```

Examples:
- `citether-mark.svg` — default production vector
- `citether-mark-responsive.svg` — scalable, no fixed dimensions
- `citether-mark-512.png` — 512×512 PNG

---

## Brand Values

| Value | Expression |
|-------|------------|
| **Precision** | Clean geometry, sharp edges, no decoration. Every element earns its place. |
| **Convergence** | The hash is where forces meet. Competing grid priorities balanced by intelligence. |
| **Clarity** | Information should be understood at a glance. Dense data, clear hierarchy. |
| **Restraint** | Subtract until only the essential remains. The brand is professional, not playful. |

---

*citEther — intelligence for the grid*
