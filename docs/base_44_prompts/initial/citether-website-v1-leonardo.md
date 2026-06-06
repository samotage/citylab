# citEther — Base44 Website Prompt (Variant 1: Leonardo)

## Design Direction: Fluid Dark SaaS

Inspired by Leonardo AI. Dark-mode dominant, particle network animations, glassmorphism cards, gradient mesh backgrounds. Premium, futuristic, tech-forward.

**Visual signature:** Dark canvas (#09090B) with glowing violet (#7C3AED) and teal (#0D9488) accents. Floating particle network in hero. Frosted glass cards with backdrop-blur. Diagonal/wave section dividers. Smooth scroll-triggered fade-up animations.

---

## Brand

**Name:** citEther (lowercase c-i-t, capital E)
**Logo:** Hashtag/grid geometric mark — interconnection symbol
**Tagline:** "Tether to the grid. Get paid."
**Fonts:** Inter for text, JetBrains Mono for numbers/data
**Colours:** Violet #7C3AED primary, Teal #0D9488 secondary, Amber #D97706 accent, Dark #09090B backgrounds, White #FFFFFF cards

---

## Page Structure (Single-Page Scrolling)

### Section 1: Hero (Full viewport, dark background)

Background: Dark (#09090B) with animated particle/node network — glowing dots (violet, teal) slowly connecting and disconnecting, representing homes joining the citEther network. Subtle gradient glow behind the headline. Particles respond to mouse position with parallax.

Content (centered):
- citEther hashtag logo (64px, white/violet)
- Headline: **"Your energy. Your value. Your community."**
- Subhead: "citEther connects your solar, battery, and EV to the grid — and puts real money in your pocket for doing it."
- CTA button: "Join your neighbourhood" (violet, rounded-full, soft glow pulse on idle)
- Secondary CTA: "See how it works" (ghost button, smooth scrolls to Section 2)
- Animated counter strip below CTAs — three stats tick up from zero on load:
  - "4.3M solar households in Australia"
  - "7 TWh of clean energy curtailed — wasted"
  - "31% of grid intervals now negative price"
- Trust strip at bottom: "Powered by NEM data" · "Real-time grid signals" · "Community-owned value"

### Section 2: The Problem (scroll-triggered, light background)

Layout: Two-column on desktop, stacked on mobile.

Left: Animated SVG illustration — a house with solar panels. Money icons float upward from the house and dissolve, representing value leaking away. A generic greyed-out energy company logo catches the money. Loops subtly.

Right:
- Eyebrow: "THE TRUST CRISIS" (uppercase, teal, 11px, tracked)
- Headline: **"You invested in solar. The energy companies invested in taking your value."**
- Body: "You spent thousands putting panels on your roof and a battery in your garage. But the system wasn't built for you. Your battery gets discharged without your consent. You export power at negative prices for nothing. And every year, the 'savings' they promised get smaller."
- Pull quote (highlighted violet border-left): "The utility death spiral is real. As more people disconnect, prices rise for everyone who stays. Everyone loses."
- Three glassmorphism stat cards in a row:
  - "7 TWh" / "Clean energy curtailed in 2025"
  - "31%" / "Intervals with negative prices"
  - "$0" / "What most households earn from flexibility"

### Section 3: How citEther Works (scroll-triggered)

Layout: Centered vertical step flow connected by animated dotted line that draws itself as you scroll.

Eyebrow: "HOW IT WORKS"
Headline: **"Three steps. Real value. No middleman."**

Three glassmorphism step cards, numbered, appear one by one with staggered 200ms fade-up:

Step 1: Connect your assets
- Icon: Animated SVG — solar panel + battery + EV connecting with glowing lines to a central citEther node
- "Link your solar inverter, home battery, or EV. citEther talks to SunRay, Enphase, Tesla Powerwall, and dozens more. One app, every asset."

Step 2: See your value in real time
- Icon: Animated mini-dashboard — price ticker, SoC gauge, flexibility value counter ticking
- "citEther reads the grid in real time. When your flexibility is worth something — a price spike, a grid stress event, a sunny midday oversupply — you see exactly what your energy is worth, right now."

Step 3: Get paid
- Icon: Animated wallet — dollar amount incrementing, notification bell ping
- "citEther optimises when your battery charges, when it discharges, and when your EV feeds the grid. You earn the margin between what the grid pays and what it costs you. Always net positive."

### Section 4: Follow Me Power (full viewport, dark gradient violet-to-teal diagonal)

This is the showpiece. Give it maximum visual weight.

Layout: Split — left is map visualisation, right is text.

Map (left, animated):
- Stylised map of Melbourne suburbs (Dandenong, Springvale, CBD marked)
- EV icon drives along a route line, stops at Dandenong — price badge appears: "$50/hr"
- EV drives to Springvale — badge updates: "$80/hr" with green "higher demand" indicator
- Glowing circles pulse at each location showing demand intensity
- 6-second animation loop

Text (right):
- Eyebrow: "HEADLINE INNOVATION"
- Badge: "Follow Me Power" (violet pill, glowing)
- Headline: **"Your EV earns money wherever you park."**
- Body: "Plug in at Dandenong, earn $50. Drive to Springvale where demand is higher, earn $80. citEther calculates the real-time value of your EV's energy at every node in the grid. You choose where to park. The grid pays you based on how much it needs you there."
- Pull quote: "It's not vehicle-to-grid. It's vehicle-to-value."
- CTA: "See Follow Me Power in action" (teal button)

### Section 5: Community (scroll-triggered, light background)

Eyebrow: "STRONGER TOGETHER"
Headline: **"Energy is better when it's local."**
Subhead: "citEther isn't just a platform — it's your neighbourhood energy cooperative. Real people. Real value. Real community."

2x2 feature grid, glassmorphism cards with hover-lift:

1. Neighbourhood Leaderboards (trophy icon) — "See how your street stacks up. Top contributors earn bonus credits and community recognition."
2. Grid Events (lightning + bell icon) — "When the grid needs help, your neighbourhood responds together. Collective action, collective reward."
3. Tips & Sharing (chat bubbles icon) — "Share what works. Which tariff plan saves most? When's the best time to charge? Community knowledge beats corporate advice."
4. Local Meetups (map pin + people icon) — "Monthly neighbourhood energy get-togethers. Learn, share, and meet the people powering your local grid."

Below: Animated testimonial strip cycling with fade — "Joined 3 weeks ago. Already earned $127." / "Our street saved 40% on winter bills."

### Section 6: The Economics (scroll-triggered)

Eyebrow: "THE MODEL"
Headline: **"The grid pays. You earn. citEther takes a margin on the value it creates."**

Animated Sankey-style flow diagram (SVG):
- Left: "Grid operator" → pays for coordinated DER
- Center: "citEther" → optimises, coordinates, settles
- Right: "You" → net positive, always

Three value cards:
1. For you: "Direct payments for flexibility. No lock-in. Transparent accounting."
2. For the grid: "Coordinated DER is cheaper than building $2B gas peakers. We make distributed energy dispatchable."
3. For the planet: "Every kWh of flexibility deployed is a kWh of fossil fuel that doesn't fire."

### Section 7: CTA / Sign-up (full viewport, dark, particle network callback)

- Headline: **"Borrow a cup of power from your neighbour."**
- Subhead: "In the old days, you'd reach over the fence for a cup of sugar. citEther makes energy just as simple."
- Email capture: Glassmorphism input + "Get early access" violet button
- Below: "No lock-in. No contracts. Just value."

### Footer

citEther logo (small) · How it works · Follow Me Power · Community · About · "Built at Watt The Hack 2026" badge

---

## Animation Summary

| Element | Animation | Trigger |
|---------|-----------|---------|
| Hero particles | Continuous drift + mouse parallax | On load |
| Stat counters | Tick up from 0 | On load |
| Step cards | Fade-up, staggered 200ms | Scroll |
| Follow Me Power map | EV route + prices | Scroll, loops |
| Feature cards | Lift + shadow | Hover |
| Testimonials | Cross-fade, 4s | Continuous |
| Section dividers | Wave/diagonal SVG | Between sections |
| CTA buttons | Soft glow pulse | Continuous |
| Demand circles | Scale breathe 1.0→1.1 | Continuous |

## Micro-interaction details

- All hover transitions: 150ms ease
- Scroll animations: IntersectionObserver trigger at 20% visibility
- Number counters: 1.5s duration, ease-out
- All animations respect prefers-reduced-motion
- Touch targets minimum 44px
