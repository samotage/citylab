# citEther — Base44 Website Prompt (Variant 2: Linear)

## Design Direction: Clean Light Editorial

Inspired by Linear and Stripe. Light-mode dominant, generous whitespace, sharp typography hierarchy, minimal animation. Authority through restraint. The anti-energy-dashboard — no dark mode cliches, no neon gradients. Confidence and clarity.

**Visual signature:** White canvas (#FAFAFA) with violet (#7C3AED) as the single accent. Monochrome illustrations with one violet highlight element per section. Large type, editorial layout, Swiss precision. Animations are subtle — opacity fades and gentle slides, never flashy.

---

## Brand

**Name:** citEther (lowercase c-i-t, capital E)
**Logo:** Hashtag/grid geometric mark — interconnection symbol
**Tagline:** "Tether to the grid. Get paid."
**Fonts:** Inter for text, JetBrains Mono for numbers/data
**Colours:** Violet #7C3AED primary (used sparingly), Zinc neutrals (#09090B text, #52525B secondary, #A1A1AA tertiary), White #FFFFFF backgrounds, Surface #F4F4F5 cards

---

## Page Structure (Single-Page Scrolling)

### Section 1: Hero (Full viewport, white background)

No particle effects. Clean, confident, quiet.

Content (centered, massive typography):
- citEther hashtag logo (48px, violet)
- Headline: **"Your energy. Your value. Your community."** (Inter 64px, -0.04em tracking, #09090B)
- Subhead: "citEther connects your solar, battery, and EV to the grid — and puts real money in your pocket for doing it." (Inter 20px, #52525B)
- CTA button: "Join your neighbourhood" (violet fill, white text, 12px radius, no glow — just a clean hover darken)
- Secondary CTA: "See how it works →" (text link, violet, arrow animates right on hover)
- Three stat blocks below CTAs in a horizontal row, separated by thin zinc-200 vertical dividers:
  - "4.3M" (JetBrains Mono 36px) / "solar households" (Inter 13px, #A1A1AA)
  - "7 TWh" (JetBrains Mono 36px) / "clean energy curtailed" (Inter 13px, #A1A1AA)
  - "31%" (JetBrains Mono 36px) / "negative price intervals" (Inter 13px, #A1A1AA)
- No trust strip. The numbers ARE the trust.

Micro-interactions:
- Stats fade in with a 300ms stagger on load
- CTA hover: background darkens to #6D28D9
- Arrow on secondary CTA slides right 4px on hover

### Section 2: The Problem (scroll-triggered)

Layout: Full-width text block, centered, max-width 720px. No illustration — the words do the work.

- Eyebrow: "THE TRUST CRISIS" (uppercase, violet, 11px, 0.08em tracking)
- Headline: **"You invested in solar. The energy companies invested in taking your value."** (Inter 40px, #09090B)
- Body paragraph: "You spent thousands putting panels on your roof and a battery in your garage. But the system wasn't built for you. Your battery gets discharged without your consent. You export power at negative prices for nothing. And every year, the 'savings' they promised get smaller." (Inter 16px, #52525B, 1.7 line-height)
- Pull quote: "The utility death spiral is real. As more people disconnect, prices rise for everyone who stays." — styled as oversized italic text (Inter 24px, italic, #09090B) with a 3px violet left border
- Three inline stat pairs below (horizontal, separated by space):
  - "7 TWh curtailed" · "31% negative intervals" · "$0 earned from flexibility"
  - All in JetBrains Mono 14px, #A1A1AA

### Section 3: How citEther Works (scroll-triggered)

Layout: Three cards in a horizontal row (desktop), stacked (mobile). Clean white cards with 1px zinc-200 border, 16px padding, 12px radius.

Eyebrow: "HOW IT WORKS"
Headline: **"Three steps. Real value. No middleman."** (Inter 36px)

Card 1: Connect your assets
- Number: "01" (JetBrains Mono 48px, violet, 0.3 opacity)
- Headline: "Connect" (Inter 20px, 700)
- Body: "Link your solar inverter, home battery, or EV. citEther talks to SunRay, Enphase, Tesla Powerwall, and dozens more. One app, every asset."
- Small icon: simple line-art plug/socket (violet stroke, no fill)

Card 2: See your value in real time
- Number: "02"
- Headline: "See value"
- Body: "citEther reads the grid in real time. When your flexibility is worth something — a price spike, a grid stress event, a sunny midday oversupply — you see exactly what your energy is worth, right now."
- Small icon: line-art chart/ticker

Card 3: Get paid
- Number: "03"
- Headline: "Get paid"
- Body: "citEther optimises when your battery charges, when it discharges, and when your EV feeds the grid. You earn the margin between what the grid pays and what it costs you. Always net positive."
- Small icon: line-art wallet

Cards have a subtle hover: border transitions to violet (#7C3AED) over 150ms.

### Section 4: Follow Me Power (light background, full width)

This section gets a very subtle #F4F4F5 surface background to differentiate from the white sections above and below.

Layout: Two-column. Left text, right map.

Text (left):
- Badge: "Follow Me Power" (violet text on violet-50 background, 10px, uppercase, pill shape)
- Headline: **"Your EV earns money wherever you park."** (Inter 36px)
- Body: "Plug in at Dandenong, earn $50. Drive to Springvale where demand is higher, earn $80. citEther calculates the real-time value of your EV's energy at every node in the grid. You choose where to park. The grid pays you based on how much it needs you there."
- Pull quote: "It's not vehicle-to-grid. It's vehicle-to-value." (Inter 20px, italic, violet left border)

Map (right):
- Clean, minimal line-art map of Melbourne suburbs on white
- Thin grey road lines, suburb labels in Inter 11px
- EV represented as a simple violet dot that moves along the route
- Price badges: clean rectangles with JetBrains Mono prices, violet border
- Dandenong: "$50/hr", Springvale: "$80/hr" (with a small green "↑" indicator)
- Animation: dot moves between locations on a 6-second loop, prices fade in as dot arrives
- No glowing circles, no gradient backgrounds — just clean cartography

### Section 5: Community (white background)

Eyebrow: "STRONGER TOGETHER"
Headline: **"Energy is better when it's local."**
Subhead: "citEther isn't just a platform — it's your neighbourhood energy cooperative."

2x2 grid of cards (white, 1px border, 12px radius):

1. Neighbourhood Leaderboards — simple line-art trophy icon (violet stroke). "See how your street stacks up. Top contributors earn bonus credits and community recognition."
2. Grid Events — line-art lightning icon. "When the grid needs help, your neighbourhood responds together. Collective action, collective reward."
3. Tips & Sharing — line-art chat icon. "Share what works. Which tariff plan saves most? When's the best time to charge? Community knowledge beats corporate advice."
4. Local Meetups — line-art map-pin icon. "Monthly neighbourhood energy get-togethers. Learn, share, and meet the people powering your local grid."

No testimonial strip. Clean and restrained.

### Section 6: The Economics

Eyebrow: "THE MODEL"
Headline: **"The grid pays. You earn. citEther takes a margin on the value it creates."**

Simple three-column layout with arrows between:
- Left card: "Grid operator" / "Pays for coordinated DER — cheaper than gas peakers"
- Center card (violet border): "citEther" / "Optimises, coordinates, settles"
- Right card: "You" / "Net positive. Always."
- Thin violet arrows flow left → center → right

Three text blocks below (no cards):
1. "For you: Direct payments. No lock-in. Transparent accounting."
2. "For the grid: Coordinated DER is cheaper than building $2B gas peakers."
3. "For the planet: Every kWh of flexibility is a kWh of fossil fuel that doesn't fire."

### Section 7: CTA (white background, centered)

- Headline: **"Borrow a cup of power from your neighbour."** (Inter 40px)
- Subhead: "In the old days, you'd reach over the fence for a cup of sugar. citEther makes energy just as simple." (Inter 18px, #52525B)
- Email input: clean bordered input field + "Get early access" violet button
- Below: "No lock-in. No contracts. Just value." (Inter 13px, #A1A1AA)

### Footer

Minimal. citEther logo · How it works · Follow Me Power · Community · About · "Watt The Hack 2026"
All Inter 13px, #A1A1AA. No social icons — just clean text links.

---

## Animation Summary

This variant uses MINIMAL animation. Restraint is the brand.

| Element | Animation | Trigger |
|---------|-----------|---------|
| Hero stats | Opacity fade-in, 300ms stagger | On load |
| Cards | Opacity + translateY(8px→0), 400ms | Scroll |
| Follow Me Power dot | Moves between locations | Scroll, loops |
| Card hover | Border colour to violet, 150ms | Hover |
| CTA arrow | translateX(0→4px), 150ms | Hover |

No particles. No glow. No glassmorphism. No gradient mesh. Just typography, whitespace, and one accent colour.
