# citEther — Base44 Website Prompt (Variant 4: Vercel Noir)

## Design Direction: Dark Minimal with Electric Accents

Inspired by Vercel, Raycast, and Arc Browser. Almost entirely dark. Extreme minimalism — no illustrations, no 3D renders, no glassmorphism. The content is the interface. Text glows. Borders glow. Data glows. Everything else is black. The aesthetic says: this is infrastructure, not a toy.

**Visual signature:** Near-black backgrounds (#0A0A0A) with razor-thin borders that glow violet on hover/focus. Text is the visual element — oversized headlines in white, data in violet monospace. Gradient text effects on key headlines (violet→teal). No rounded corners beyond 8px. Grid lines as decorative elements — literal grids referencing the energy grid and the hashtag logo.

---

## Brand

**Name:** citEther (lowercase c-i-t, capital E)
**Logo:** Hashtag/grid geometric mark — rendered as thin white lines on dark, glowing violet on hover
**Tagline:** "Tether to the grid. Get paid."
**Fonts:** Inter for text, JetBrains Mono for numbers/data
**Colours:** Violet #7C3AED (electric accent), Teal #0D9488 (secondary glow), Near-black #0A0A0A backgrounds, #18181B card surfaces, #27272A borders, #FAFAFA text, #A1A1AA secondary text

---

## Page Structure (Single-Page, Dark Throughout)

### Section 1: Hero (Full viewport)

Background: #0A0A0A. A subtle grid pattern (thin #18181B lines, 60px spacing) covers the entire background — referencing both the energy grid and the hashtag logo. One grid intersection point in the center glows violet with a soft radial gradient.

Content (centered):
- citEther logo (48px, white lines, the hashtag mark)
- Headline: **"Your energy. Your value. Your community."** — gradient text effect, violet (#7C3AED) to teal (#0D9488), left to right. Inter 64px, 800 weight.
- Subhead: "citEther connects your solar, battery, and EV to the grid — and puts real money in your pocket for doing it." (Inter 18px, #A1A1AA)
- CTA: "Join your neighbourhood" — white text on transparent, 1px violet border, 8px radius. On hover: background fills violet, border glows with 0 4px 20px rgba(124,58,237,0.4) box-shadow.
- Secondary: "See how it works ↓" — #A1A1AA text, violet on hover

Three stat blocks below, separated by thin vertical #27272A lines:
- "4.3M" (JetBrains Mono 40px, violet) / "solar households" (Inter 12px, #A1A1AA)
- "7 TWh" (JetBrains Mono 40px, violet) / "curtailed — wasted" (Inter 12px, #A1A1AA)
- "31%" (JetBrains Mono 40px, violet) / "negative price intervals" (Inter 12px, #A1A1AA)

### Section 2: The Problem

Background: #0A0A0A continues. No section break — just a thin horizontal #27272A line as separator.

Layout: Left-aligned text, max-width 640px, with generous left margin (20% of viewport).

- Eyebrow: "THE TRUST CRISIS" (JetBrains Mono 11px, violet, uppercase, 0.1em tracking)
- Headline: **"You invested in solar. The energy companies invested in taking your value."** (Inter 36px, #FAFAFA)
- Body: "Your battery gets discharged without your consent. You export power at negative prices for nothing. And every year, the 'savings' they promised get smaller." (Inter 16px, #A1A1AA, 1.8 line-height)
- Pull quote: "The utility death spiral is real." — Inter 28px, italic, gradient text violet→teal

Below the text, three inline data points in a monospace strip:
```
7 TWh curtailed    ·    31% negative    ·    $0 earned
```
JetBrains Mono 13px, #A1A1AA, letter-spaced. The dots are violet.

### Section 3: How It Works

Three horizontal cards stacked vertically with thin #27272A borders. Each card is full-width, 120px height, with content left-aligned.

Eyebrow: "HOW IT WORKS"
Headline: **"Three steps. Real value. No middleman."** (Inter 32px)

Card 1:
- Left: "01" (JetBrains Mono 48px, #27272A — very subtle)
- Center: "Connect your assets" (Inter 18px, 600, white) + "One app. SunRay, Enphase, Tesla, dozens more." (Inter 14px, #A1A1AA)
- Right: → arrow icon (violet)
- Hover: entire card border glows violet, box-shadow 0 0 20px rgba(124,58,237,0.15)

Card 2:
- "02" / "See your value in real time" + "Price spikes, grid stress, surplus — your flexibility priced to the minute." / →

Card 3:
- "03" / "Get paid" + "Always net positive. The margin between grid value and your cost." / →

### Section 4: Follow Me Power

Full viewport. This section gets a special treatment — the grid background pattern intensifies here, with multiple intersection points glowing (violet and teal) to represent network nodes.

Layout: Centered.

- Badge: "Follow Me Power" — JetBrains Mono 11px, violet text, 1px violet border pill, glowing box-shadow
- Headline: **"Your EV earns money wherever you park."** — gradient text, Inter 48px

Below headline: a minimal terminal/console-style display showing the Follow Me Power concept:

```
┌─────────────────────────────────────────────┐
│  LOCATION        DEMAND    VALUE    STATUS   │
│  ─────────────────────────────────────────── │
│  Dandenong       ████░░    $50/hr   ● LIVE   │
│  Springvale      ██████    $80/hr   ● LIVE   │
│  Caulfield       ███░░░    $42/hr   ● LIVE   │
│  CBD             █████░    $67/hr   ● LIVE   │
└─────────────────────────────────────────────┘
```

JetBrains Mono throughout. Borders are #27272A. Values are violet. LIVE dots are teal, pulsing. The demand bars fill/empty with a subtle animation on a 4-second cycle to show changing demand.

Below the terminal display:
- Body: "Plug in at Dandenong, earn $50. Drive to Springvale where demand is higher, earn $80. citEther calculates real-time locational value across the network." (Inter 16px, #A1A1AA)
- Pull quote: "It's not vehicle-to-grid. It's vehicle-to-value." (Inter 20px, italic, white)

### Section 5: Community

Four feature rows (not cards — just text rows with thin separators). Minimal, list-style.

Eyebrow: "STRONGER TOGETHER"
Headline: **"Energy is better when it's local."**

Each row: icon (violet line-art, 20px) + title (Inter 16px, white) + description (Inter 14px, #A1A1AA) — all on one line, left-aligned.

- ◆ Leaderboards — "See how your street stacks up. Earn bonus credits."
- ◆ Grid Events — "Your neighbourhood responds together. Collective reward."
- ◆ Tips & Sharing — "Community knowledge beats corporate advice."
- ◆ Local Meetups — "Monthly get-togethers. Real people, real value."

Rows have a hover: background shifts to #18181B. Clean, understated.

### Section 6: The Economics

Headline: **"The grid pays. You earn. citEther takes a margin."**

A horizontal flow rendered as three inline blocks connected by arrows:

[ Grid operator ] ——→ [ citEther ] ——→ [ You ]

Each block: #18181B background, 1px #27272A border, 8px radius. Labels in Inter 14px white. Arrows are thin violet lines with animated dash-array (flowing left-to-right). The citEther block has a violet border.

Three lines below (no cards):
- "For you — direct payments, no lock-in, transparent accounting." (#A1A1AA)
- "For the grid — coordinated DER, cheaper than gas peakers." (#A1A1AA)
- "For the planet — every kWh of flexibility replaces a kWh of fossil fuel." (#A1A1AA)

### Section 7: CTA

Centered on dark background. The grid pattern returns.

- Headline: **"Borrow a cup of power from your neighbour."** (Inter 40px, white)
- Subhead: "In the old days, you'd reach over the fence for a cup of sugar. citEther makes energy just as simple." (Inter 16px, #A1A1AA)
- Email input: dark #18181B background, 1px #27272A border, focus glow violet. + "Get early access" button (1px violet border, violet text, fills violet on hover)
- "No lock-in. No contracts. Just value." (Inter 12px, #52525B)

### Footer

#0A0A0A background. Thin #27272A top border.
citEther logo (small, white) · text links in #A1A1AA · "Watt The Hack 2026" in #52525B
Minimal. No decorative elements.

---

## Animation Summary

This variant uses STRUCTURAL animation — glowing borders, pulsing dots, flowing dashes. No scroll-triggered fades, no particle effects, no parallax.

| Element | Animation | Trigger |
|---------|-----------|---------|
| Grid intersection glow | Soft pulse (opacity 0.3→0.6) | Continuous |
| Stats | Counter tick-up | On load |
| How It Works cards | Border glow on hover | Hover |
| Follow Me Power bars | Fill level changes | 4s cycle, continuous |
| LIVE dots | Opacity pulse | Continuous |
| Economics arrows | Dash-array flow left→right | Continuous |
| CTA input | Border glow violet on focus | Focus |
| Badge | Box-shadow glow | Continuous subtle |

## Key Differentiator from Other Variants

No illustrations. No 3D. No glassmorphism. No gradients except text. The grid pattern IS the brand — it references the energy grid, the hashtag logo, and the network topology simultaneously. The terminal-style Follow Me Power display says "this is real infrastructure" more convincingly than any animated map. This variant appeals to the most technically-minded judges.
