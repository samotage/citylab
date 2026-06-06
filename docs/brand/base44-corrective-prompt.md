# citEther — Base44 Corrective Rebuild

## CRITICAL: Read this entire prompt before changing anything.

The current site is generic AI landing page slop. Every section is centered text + cards. The colour palette is wrong. The typography has no personality. It looks like every other AI-generated SaaS page. This prompt fixes that.

---

## What's Wrong (Do NOT repeat these mistakes)

1. **Wrong colours.** You used violet (#7C3AED) everywhere. That is NOT a citEther brand colour. Remove ALL violet from the site. The actual palette is below.
2. **Card soup.** Every section resolves to a grid of rounded-corner cards with light borders. That's the #1 tell of an AI-generated landing page. Break this pattern.
3. **Centred everything.** Every section is centered text on white. No asymmetry, no editorial tension, no visual rhythm.
4. **Massive dead whitespace.** Sections have enormous unintentional gaps. The spacing has no rhythm — it feels unfinished, not restrained.
5. **Generic icons.** Purple outline icons (star, lightning, chat, pin) are stock AI icon choices. Remove them or redesign.
6. **The map is a grey grid.** The Follow Me Power "map" looks like a placeholder. It needs to look like an actual stylised map of Melbourne's south-east.
7. **Missing content.** The shared content layer specifies consumer quotes, Auto-Arb engine detail, a citEther Pod section, a compatibility strip, and social norming detail. None of it is in the current build.
8. **The wordmark is wrong.** "citEther" should have "cit" in Amber (#E8A838) and "Ether" in Deep Teal (#0D7377) — NOT a violet "E".

---

## Brand Palette (USE THESE — not violet)

### Primary

| Name | Hex | Usage |
|------|-----|-------|
| **Amber** | `#E8A838` | Primary accent. CTAs, highlights, key data, the "energy" colour. The warm, active pulse. |
| **Charcoal** | `#2D2926` | Primary dark. Body text, dark section backgrounds, headers. The "infrastructure" colour. |
| **Deep Teal** | `#0D7377` | Secondary accent. Interactive elements, data highlights, the "intelligence/ether" colour. |

### Supporting

| Name | Hex | Usage |
|------|-----|-------|
| **White** | `#FFFFFF` | Light section backgrounds, card surfaces |
| **Warm Grey** | `#8A8480` | Secondary text, metadata, borders, subtle elements |
| **Amber Light** | `#F5D08A` | Hover states, light amber fills, subtle warmth |
| **Teal Light** | `#4DA8AB` | Secondary data, positive indicators |
| **Charcoal Light** | `#4A4542` | Subtle borders, dark mode card backgrounds |
| **Signal Red** | `#D94F4F` | Alerts, negative price events only — NOT decorative |
| **Signal Green** | `#4CAF50` | Positive states only — NOT decorative |

### Colour Rules

- **Remove ALL violet/purple** (#7C3AED, #6D28D9, etc.) from every element
- Amber + Charcoal is the primary brand expression — when only two colours are available, use these
- Deep Teal is the digital accent — use for interactive elements, links, data highlights
- Never use amber on teal (insufficient contrast). Amber on charcoal or white; teal on charcoal or white
- Signal colours (red/green) for data states only, never decorative

---

## The citEther Wordmark

When rendering the brand name in the nav and anywhere it appears:
- **"cit"** in Amber (#E8A838)
- **"Ether"** in Deep Teal (#0D7377)
- On dark backgrounds: "cit" in Amber, "Ether" in White
- The "E" is always uppercase. Never render as "Citether", "CITETHER", or "citether"

The hashtag logo mark uses amber diagonal bars and charcoal horizontal bars. NOT violet.

---

## Typography

- **Headlines:** Inter 700, tight tracking (-0.03em). Charcoal (#2D2926) on light, White on dark.
- **Body:** Inter 400, 1.6 line-height. Body Text #3D3835 on light, #D4D0CC on dark.
- **Data/numbers:** JetBrains Mono 600. Amber (#E8A838) for emphasis numbers, Charcoal for standard.
- **Eyebrow labels:** JetBrains Mono 500, 11px, 0.12em tracking, uppercase. Deep Teal (#0D7377) — NOT violet.
- **Pull quotes:** Inter 400 italic, 22px, with a 3px Amber left border.

---

## Design Direction: Editorial Grid, Not AI Card Soup

**The aesthetic is Monocle magazine meets Bloomberg Terminal.** Dense, confident, editorial. Information-rich, not whitespace-padded. Think the visual authority of an infrastructure company, not the bubbly optimism of a consumer SaaS app.

### Layout Principles

1. **Alternate dark and light sections.** Not all-white. Use Charcoal (#2D2926) backgrounds for at least the hero and one mid-page section to create visual rhythm and contrast.
2. **Break symmetry.** Left-heavy text blocks. Right-aligned data. Offset grids. Not every section centered. At least 3 sections should use asymmetric two-column layouts.
3. **Dense, not padded.** Section padding should be 80-100px vertical, not 200px+. The current site has sections drowning in whitespace. Tighten.
4. **Rule lines, not card borders.** Use thin horizontal rules (1px, Warm Grey #8A8480, 0.3 opacity) to separate content instead of putting everything in bordered cards. When cards ARE used, they should have no border-radius greater than 4px and use subtle background tints, not visible borders.
5. **Editorial typography scale.** Hero headline at 72-80px. Section headlines at 40-48px. Let the type do the work — not cards, not icons, not decorative elements.

### What NOT to do

- No border-radius: 12px cards everywhere
- No purple/violet anything
- No generic line-art icons as the primary visual for a section
- No 2x2 card grids (the community section's current layout)
- No massive empty gaps between sections
- No gradient mesh backgrounds
- No glassmorphism
- No particle effects
- No generic "01 02 03" step numbers at 48px with 0.3 opacity — that's an AI-generated landing page cliche

---

## Page Structure (Complete Rebuild)

### Section 1: Hero (Dark — Charcoal #2D2926 background)

The hero is dark. It's the first thing people see and it needs to say "this is not another pastel SaaS app."

**Layout:** Full viewport height. Left-aligned headline (not centered). Stats row at the bottom of the viewport.

**Elements:**
- **Nav bar** (fixed, transparent on hero, solid on scroll):
  - Left: citEther wordmark ("cit" in Amber, "Ether" in White on dark)
  - Right: How it works · Follow Me Power · Community · Economics
  - Far right: "Get early access" button — Amber fill (#E8A838), Charcoal text (#2D2926), border-radius: 4px, font-weight: 600
- **Eyebrow:** "DISTRIBUTED ENERGY · REAL-TIME VALUE" — JetBrains Mono, 11px, Amber (#E8A838), 0.12em tracking
- **Headline:** "Your energy. Your value. Your community." — Inter 700, 72px on desktop, White (#FFFFFF). Left-aligned, max-width: 800px. "Your community." on its own line, in Amber (#E8A838)
- **Subhead:** "citEther connects your solar, battery, and EV to the grid — and puts real money in your pocket for doing it." — Inter 400, 20px, #8A8480
- **Primary CTA:** "Join your neighbourhood" — Amber fill, Charcoal text, 4px radius, 16px padding
- **Secondary CTA:** "See how it works →" — text link, Deep Teal, arrow slides right 4px on hover
- **Stats row** (bottom of hero, separated by thin Charcoal Light vertical dividers):
  - "4.3M" / "solar households" — JetBrains Mono 36px Amber / Inter 12px Warm Grey
  - "7 TWh" / "clean energy curtailed" — same treatment
  - "31%" / "negative price intervals" — same treatment

**Background detail:** A very subtle grid pattern (1px lines at ~60px intervals, #3D3835, 0.15 opacity) covering the hero. Not a particle network. Not animated. Just a quiet nod to the grid.

**Animations:** Stats counter ticks from 0 to value on load (800ms, ease-out). Headline fades in from opacity 0 to 1 over 600ms. No other animation.

---

### Section 2: The Problem (Light background — #FAFAFA)

**Layout:** Two-column. Left: consumer voice quotes (the evidence). Right: editorial text (the argument). Max-width: 1200px.

**Left column — Real consumer voices (the primary content):**

Stack 3 quote blocks vertically, each with:
- Quote text in Inter 400 italic, 20px, Charcoal (#2D2926)
- Context line below: "— Australian solar owner on managing wholesale prices" in JetBrains Mono 11px, Warm Grey
- 3px Amber left border on each quote
- No card border, no card background — just the amber rule and typography

**Quotes to use (verbatim):**
1. "I already have a full time job." — on babysitting wholesale prices
2. "My family erased the entire year's savings in one day" — one hot day, AC through a price spike
3. "All of the ones you listed lock you down to the brand's components" — on inverter ecosystem lock-in

**Right column — The argument:**
- Eyebrow: "THE TRUST CRISIS" — JetBrains Mono, 11px, Deep Teal, uppercase
- Headline: "You invested in solar. The energy companies invested in taking your value." — Inter 700, 36px, Charcoal
- Body: "You spent thousands putting panels on your roof and a battery in your garage. But the system wasn't built for you. Your battery gets discharged without your consent. You export power at negative prices. And every year, the 'savings' they promised get smaller." — Inter 400, 16px, #3D3835

**Stat line** (below both columns, full width, separated by middots):
"7 TWh curtailed · 31% negative intervals · $0 earned from flexibility · Feed-in tariffs: 15c → 12c → 8c" — JetBrains Mono 13px, Warm Grey

---

### Section 3: How It Works — The Auto-Arb Engine (Light background)

**Do NOT use the "01 02 03" card pattern.** Instead, this is an editorial explainer with a visual diagram.

**Layout:** Section headline spanning full width. Below: two-column. Left: the Auto-Arb engine explanation. Right: a simple flow diagram (text-based, not illustrated).

**Headline area:**
- Eyebrow: "HOW IT WORKS" — JetBrains Mono, Deep Teal
- Headline: "Set it. Forget it. Get paid." — Inter 700, 44px

**Left column — The engine:**
Three steps presented as a vertical sequence with thin connecting rules between them (not cards):

**Connect** (Inter 600, 20px, Charcoal)
"Link your solar inverter, home battery, or EV. citEther talks to Fronius, Enphase, Tesla Powerwall, GoodWe, Sigenergy — brand-agnostic, not locked to one ecosystem."

↓ (thin 1px Warm Grey vertical line, 24px)

**Optimise** (Inter 600, 20px, Charcoal)
"The Auto-Arb engine reads the grid in real time — price signals, solar forecasts, grid stress events — and makes dispatch decisions automatically. Charges when power is cheapest, discharges at peak rates. Comfort guardrails mean one hot day can't erase a year's savings."

↓

**Earn** (Inter 600, 20px, Charcoal)
"No babysitting. No watching wholesale prices for 12 hours a day. Clear reports show what you earned and why. Always net positive."

**Right column — Visual:**
A minimal flow diagram (text and lines, not an illustration):
```
Solar → Battery → Grid (peak)
         ↕
       EV ← Grid (off-peak)
         ↕
      Hot Water
```
Rendered as connected text labels with thin directional lines. Amber for "earning" flows (Battery → Grid). Teal for "intelligence" flows. Charcoal for labels. Think Bloomberg terminal diagram, not infographic.

---

### Section 3b: Compatibility Strip (immediately after How It Works)

A single horizontal band, subtle — not a section, just a confidence strip.

**Background:** #F4F4F5

**Content (horizontal scroll on mobile, single row on desktop):**
- Label: "WORKS WITH" — JetBrains Mono, 11px, Warm Grey
- Brand names in a row, separated by thin vertical dividers: Fronius · Enphase · GoodWe · Sigenergy · Sungrow · SMA · Tesla Powerwall · BYD · Alpha ESS · Zappi · Wallbox
- All names in Inter 400, 13px, Warm Grey (#8A8480) — muted, not prominent
- Below: "Modbus TCP · MQTT · Local API — no forced cloud" — JetBrains Mono, 11px, Warm Grey

---

### Section 4: Follow Me Power (Dark — Charcoal #2D2926 background)

This section is dark to create rhythm (light-dark-light-dark pattern). This is the "wow" section.

**Layout:** Two-column. Left: text. Right: stylised map.

**Left column:**
- Badge: "FOLLOW ME POWER" — JetBrains Mono, 11px, Amber, with a subtle Amber/transparent background pill
- Headline: "Your EV earns money wherever you park." — Inter 700, 40px, White
- Body text in #D4D0CC
- Pull quote: "It's not vehicle-to-grid. It's vehicle-to-value." — Inter italic, 20px, Amber, with 3px Amber left border

**Right column — The map:**
A stylised map of Melbourne's south-east suburbs. NOT a grey grid — an actual recognisable map outline.

- Dark background matches section (#2D2926)
- Road lines in Charcoal Light (#4A4542), 1px
- Suburb labels: "Dandenong", "Clayton", "Springvale" — Inter 11px, Warm Grey
- EV dot: Amber (#E8A838), 12px diameter, with a soft 20px amber glow
- Price badges: rounded rectangles with Amber border, Charcoal fill. "$50/hr" / "$80/hr" in JetBrains Mono, Amber text. The higher price gets a green "↑" indicator
- EV dot animates between locations on a 6-second loop
- Dotted amber route line connecting the locations

**Below map:** "Melbourne metropolitan grid · illustrative pricing · NEM nodal data" — JetBrains Mono 11px, Warm Grey

---

### Section 5: citEther Pod — Your Street as a Microgrid (Light background)

**This is a NEW section.** It goes between Follow Me Power and Community.

**Layout:** Full-width headline, then two-column. Left: visual. Right: text.

**Headline:**
- Eyebrow: "CITETHER POD" — JetBrains Mono, Deep Teal
- Headline: "Your street. Your microgrid. Your rules." — Inter 700, 44px

**Left column — Visual:**
A bird's-eye or isometric illustration (CSS/SVG, not an image) of a suburban street showing 6-8 houses. Animated energy flow lines:
- Solar from House A flowing to House B's battery (amber lines)
- House C's EV charging from House D's surplus (teal lines)
- A dotted boundary around the street (the "pod boundary") in Amber
- Outside the boundary: a single calm connection to "THE GRID" (thin, grey)
- Inside the boundary: active flows between houses (amber and teal)
- Key message: lots of local activity, minimal grid interaction

**Right column — Text:**
"A citEther Pod is a group of co-located households — your apartment building, your street, your cul-de-sac — who form a cooperative and self-manage energy at the distribution node level."

Four benefits as a vertical list with thin Amber left rules (not cards, not icons):
- "Reduced losses" — energy consumed where it's generated doesn't travel through the transmission network. NEM losses average 5-10%.
- "Lower cost" — locally shared energy avoids network charges (40-50% of a retail bill).
- "Grid relief" — a pod that self-balances means a calmer, flatter load for the DNSP.
- "Community resilience" — in an outage, a pod with sufficient capacity can island.

---

### Section 6: Community (Light background)

**Do NOT use the 2x2 card grid.** Instead, use an editorial layout.

**Layout:** Left-heavy asymmetric. Headline and primary feature on the left (60% width). Two secondary features stacked on the right (40% width).

**Headline:**
- Eyebrow: "STRONGER TOGETHER" — JetBrains Mono, Deep Teal
- Headline: "Energy is better when it's local." — Inter 700, 44px

**Primary feature (left, large):**
"How's your street doing?" — Inter 600, 24px, Charcoal
"citEther shows how your household's grid contribution compares to similar homes in your postcode — same roof size, same battery capacity, same household type. Not to shame. To motivate." — Inter 400, 16px

Below: a compact example display (text-based, not a screenshot):
```
Your street averaged $38/month
You earned $52 — Top 15%
8 consecutive grid events responded ●●●●●●●●
```
In JetBrains Mono, Amber numbers, Charcoal labels.

**Secondary features (right, stacked):**
Each is a text block with an Amber top rule (2px), not a card:
- "Grid Events" — "When the grid needs help, your neighbourhood responds together. 87% of your street participated — will you?"
- "Seasonal Challenges" — "Winter Flex Challenge: can your street beat last year's contribution? Community knowledge beats corporate advice."

---

### Section 7: Economics / The Model (Light background with subtle #F9F8F7 tint)

**Layout:** Full-width flow diagram (not three cards with arrows).

**Headline:**
- Eyebrow: "THE MODEL" — JetBrains Mono, Deep Teal
- Headline: "The grid pays. You earn. citEther takes a margin on the value it creates." — Inter 700, 40px

**Flow diagram (horizontal, full-width):**
Three connected blocks with directional arrows. NOT bordered cards — use background fills:

GRID OPERATOR (Charcoal fill, white text) → CITETHER (Amber fill, Charcoal text) → YOU (Teal fill, white text)

Each block: label in JetBrains Mono 11px uppercase at top, description in Inter 400, 14px below.
Arrows: thin Warm Grey lines with arrowheads.

**Three revenue streams** (below, horizontal row, no cards — just three text blocks separated by vertical rules):

"FOR YOU" (Amber, JetBrains Mono 11px)
"Direct payments. Savings-share model — citEther takes a margin on the delta. You always net positive."

"FOR THE GRID" (Deep Teal)
"Coordinated DER is cheaper than gas peakers ($2B+ per facility). 100,000 managed batteries beat one peaking plant."

"FOR THE PLANET" (Charcoal)
"Every kWh of flexibility is a kWh of fossil fuel that doesn't fire."

---

### Section 8: CTA (Dark — Charcoal #2D2926 background)

**Layout:** Centered, tight.

- Headline: "Borrow a cup of power from your neighbour." — Inter 700, 44px, White
- Subhead: "In the old days, you'd reach over the fence for a cup of sugar. citEther makes energy just as simple." — Inter 400, 18px, Warm Grey
- Email input: Charcoal Light background, White text, Inter 400. Rounded-left.
- Button: "Get early access" — Amber fill, Charcoal text, 4px radius. Joined to input right side.
- Below: "No lock-in · No contracts · Just value" — JetBrains Mono 12px, Warm Grey

---

### Footer (Dark — #1a1a1a background, even darker than hero)

Minimal, single row:
- Left: citEther wordmark (cit in Amber, Ether in White)
- Center: How it works · Follow Me Power · Community · Economics · About — Inter 13px, Warm Grey, separated by middots
- Right: "Watt The Hack 2026" — JetBrains Mono 11px, Warm Grey
- Below: "© 2026 citEther" — Inter 11px, #4A4542

---

## Animation Rules

Restraint. These are the ONLY animations permitted:

| Element | Animation | Trigger |
|---------|-----------|---------|
| Hero stats | Counter tick 0→value, 800ms ease-out | Page load |
| Hero headline | Opacity 0→1, 600ms | Page load |
| Section content | Opacity + translateY(12px→0), 500ms | Scroll into view |
| Follow Me Power EV dot | Moves between locations | 6-second loop |
| Price badges | Fade in as EV dot arrives | Synced to dot |
| Card/block hover | Border-colour or background tint shift, 150ms | Hover |
| CTA button hover | Background darkens slightly, 100ms | Hover |

NO particle effects. NO gradient mesh. NO glassmorphism. NO parallax. NO floating elements. NO glow effects. NO wave dividers.

---

## Anti-Convergence Checklist

Before shipping, check every item:

- [ ] Zero violet/purple anywhere on the page
- [ ] Amber (#E8A838) is the primary accent, not a secondary colour
- [ ] Wordmark uses Amber "cit" + Teal "Ether" (or Amber + White on dark)
- [ ] At least 2 sections have dark (Charcoal) backgrounds
- [ ] At least 3 sections use asymmetric layouts (not centered)
- [ ] No 2x2 or 3-column card grids with rounded corners and light borders
- [ ] No generic outline icons used as primary section visuals
- [ ] The "How It Works" section does NOT use "01 02 03" in giant faded numbers
- [ ] Consumer quotes from the shared content layer are present in the Problem section
- [ ] The Auto-Arb engine is explained (not just "connect, see value, get paid")
- [ ] The citEther Pod section exists
- [ ] The compatibility strip exists
- [ ] Section padding is 80-100px, not 200px+
- [ ] The map in Follow Me Power looks like Melbourne suburbs, not a grey grid
