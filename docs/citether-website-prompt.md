# citEther — Base44 Website Builder Prompt

## Brand Identity

**Name:** citEther (lowercase c-i-t, capital E)
**Tagline:** "Tether to the grid. Get paid."
**Concept:** Urban energy communities physically and economically connected. Consumers plug in their EVs, connect their batteries, link their solar — and citEther makes it worthwhile.

**Logo:** Hashtag/grid mark — a geometric grid symbol suggesting interconnection, nodes, and networked energy. The logomark should sit comfortably at 32px in the nav and 64px on the hero.

**Colour palette:**
- Primary: Electric violet `#7C3AED` (energy, premium, trust)
- Secondary: Teal `#0D9488` (renewable, growth, positive value)
- Accent: Amber `#D97706` (energy/solar warmth, earnings highlights)
- Dark: `#09090B` (text, hero backgrounds)
- Light: `#FAFAFA` (backgrounds)
- Card: `#FFFFFF`
- Surface: `#F4F4F5`

**Typography:**
- Headlines: Inter, 700 weight, tight letter-spacing
- Body: Inter, 400–500 weight
- Data/numbers: JetBrains Mono, 600 weight (for earnings, kWh, dollar amounts)

---

## Design Direction

**Inspiration: Leonardo AI website aesthetic.** Fluid, dynamic, modern SaaS landing page with:
- Smooth scroll-triggered animations (elements fade-up, slide-in as you scroll)
- Floating/parallax elements — subtle battery icons, solar panel silhouettes, EV outlines drifting in background layers
- Gradient mesh backgrounds — violet-to-teal gradients with soft glow effects behind key sections
- Glass-morphism cards (frosted glass effect with backdrop-blur) for feature highlights
- Micro-interactions on hover: cards lift with subtle shadow, buttons pulse gently, value counters tick up
- Animated SVG illustrations (not stock photos) — stylised homes, EVs at charging stations, community networks
- Number counters that animate up when they scroll into view (e.g., "$847 earned this month" ticks from 0 to 847)
- Smooth section transitions with diagonal or wave-shaped dividers between sections
- Particle/node network animation in the hero — dots connecting to represent the citEther network

---

## Page Structure (Single-Page Scrolling)

### Section 1: Hero (Full viewport)

**Background:** Dark (`#09090B`) with animated particle network — glowing dots (violet, teal) slowly connecting and disconnecting, representing homes joining the citEther network. Subtle gradient glow behind the headline.

**Content (centered):**
- citEther logo (64px, white/violet)
- Headline: **"Your energy. Your value. Your community."**
- Subhead: "citEther connects your solar, battery, and EV to the grid — and puts real money in your pocket for doing it."
- CTA button: "Join your neighbourhood" (violet, rounded, glowing hover effect)
- Secondary CTA: "See how it works" (ghost button, scrolls to Section 2)
- Below CTAs: animated counter strip — three stats fading in:
  - "4.3M solar households in Australia"
  - "7 TWh of clean energy curtailed — wasted"
  - "31% of grid intervals now negative price"
- Trust strip at bottom of hero: small logos/badges — "Powered by NEM data" · "Real-time grid signals" · "Community-owned value"

**Micro-interactions:**
- Particle network responds subtly to mouse position (parallax)
- Stats counter animates on load (ticks up from 0)
- CTA button has a soft violet pulse animation

---

### Section 2: The Problem (scroll-triggered)

**Layout:** Two-column on desktop, stacked on mobile. Left: animated illustration. Right: text.

**Illustration (left):** Animated SVG of a house with solar panels. Money icons float away from the house upward and dissolve — representing value leaking away. An energy company logo (generic, greyed out) catches the money. The animation loops subtly.

**Text (right):**
- Eyebrow: "THE TRUST CRISIS" (uppercase, teal, 11px, tracked)
- Headline: **"You invested in solar. The energy companies invested in taking your value."**
- Body: "You spent thousands putting panels on your roof and a battery in your garage. But the system wasn't built for you. Your battery gets discharged without your consent. You export power at negative prices for nothing. And every year, the 'savings' they promised get smaller."
- Pull quote (highlighted in violet): "The utility death spiral is real. As more people disconnect, prices rise for everyone who stays. Everyone loses."
- Stat cards (glass-morphism, row of 3):
  - "7 TWh" / "Clean energy curtailed in 2025"
  - "31%" / "Intervals with negative prices"
  - "$0" / "What most households earn from flexibility"

---

### Section 3: How citEther Works (scroll-triggered)

**Layout:** Centered, with a vertical step flow connected by an animated dotted line.

**Eyebrow:** "HOW IT WORKS"
**Headline:** **"Three steps. Real value. No middleman."**

**Step cards** (glass-morphism, numbered, appear one by one as you scroll):

**Step 1: Connect your assets**
- Icon: Animated SVG — solar panel + battery + EV connecting with glowing lines to a central citEther node
- Text: "Link your solar inverter, home battery, or EV. citEther talks to SunRay, Enphase, Tesla Powerwall, and dozens more. One app, every asset."

**Step 2: See your value in real time**
- Icon: Animated dashboard mockup — price ticker, battery state-of-charge gauge, "flexibility value" counter ticking up
- Text: "citEther reads the grid in real time. When your flexibility is worth something — a price spike, a grid stress event, a sunny midday oversupply — you see exactly what your energy is worth, right now."

**Step 3: Get paid**
- Icon: Animated wallet/account — dollar amount incrementing, notification bell pinging
- Text: "citEther optimises when your battery charges, when it discharges, and when your EV feeds the grid. You earn the margin between what the grid pays and what it costs you. Always net positive."

---

### Section 4: Follow Me Power (hero feature — full viewport)

**Background:** Gradient — dark violet to teal, diagonal. This is the showpiece section.

**Layout:** Split — left side is a map visualisation, right side is the value proposition.

**Map visualisation (left, animated):**
- Stylised map of Melbourne suburbs (Dandenong, Springvale, CBD marked)
- An EV icon drives along a route line, stopping at Dandenong — a price badge appears: "$50/hr"
- The EV then drives to Springvale — the price badge updates: "$80/hr" with a green "higher demand" indicator
- Glowing circles pulse at each location showing grid demand intensity
- The animation loops with a 6-second cycle

**Text (right):**
- Eyebrow: "HEADLINE INNOVATION"
- Badge: "Follow Me Power" (violet pill, glowing)
- Headline: **"Your EV earns money wherever you park."**
- Body: "Plug in at Dandenong, earn $50. Drive to Springvale where demand is higher, earn $80. citEther calculates the real-time value of your EV's energy at every node in the grid. You choose where to park. The grid pays you based on how much it needs you there."
- Pull quote: "It's not vehicle-to-grid. It's vehicle-to-value."
- CTA: "See Follow Me Power in action" (teal button)

**Micro-interactions:**
- Map price badges pulse when the EV arrives
- Demand circles breathe (scale up/down slowly)
- Route line draws itself as the EV moves

---

### Section 5: Community (scroll-triggered)

**Layout:** Centered headline, then a 2x2 feature grid (glass-morphism cards).

**Eyebrow:** "STRONGER TOGETHER"
**Headline:** **"Energy is better when it's local."**
**Subhead:** "citEther isn't just a platform — it's your neighbourhood energy cooperative. Real people. Real value. Real community."

**Feature cards (2x2 grid, hover-lift effect):**

1. **Neighbourhood Leaderboards**
   - Icon: Trophy/podium
   - Text: "See how your street stacks up. Top contributors earn bonus credits and community recognition."

2. **Grid Events**
   - Icon: Lightning bolt + notification bell
   - Text: "When the grid needs help, your neighbourhood responds together. Collective action, collective reward."

3. **Tips & Sharing**
   - Icon: Chat bubbles
   - Text: "Share what works. Which tariff plan saves most? When's the best time to charge? Community knowledge beats corporate advice."

4. **Local Meetups**
   - Icon: Map pin + people
   - Text: "Monthly neighbourhood energy get-togethers. Learn, share, and meet the people powering your local grid."

**Below the grid:** Animated testimonial/social proof strip — "Joined 3 weeks ago. Already earned $127." / "Our street saved 40% on winter bills." (These cycle through with a fade transition.)

---

### Section 6: The Economics (scroll-triggered)

**Layout:** Centered, with an animated Sankey-style flow diagram.

**Eyebrow:** "THE MODEL"
**Headline:** **"The grid pays. You earn. citEther takes a margin on the value it creates."**

**Flow diagram (animated SVG):**
- Left: "Grid operator" → pays for coordinated DER (cheaper than building peakers)
- Center: "citEther" → optimises, coordinates, settles
- Right: "You" → net positive, always

**Three value cards below:**
1. **For you:** "Direct payments for flexibility. No lock-in. Transparent accounting."
2. **For the grid:** "Coordinated DER is cheaper than building $2B gas peakers. We make distributed energy dispatchable."
3. **For the planet:** "Every kWh of flexibility deployed is a kWh of fossil fuel that doesn't fire."

---

### Section 7: CTA / Sign-up (Full viewport)

**Background:** Dark, particle network animation (callback to hero).

**Content (centered):**
- Headline: **"Borrow a cup of power from your neighbour."**
- Subhead: "In the old days, you'd reach over the fence for a cup of sugar. citEther makes energy just as simple."
- Email capture: Glassmorphism input field + "Get early access" button (violet)
- Below: "No lock-in. No contracts. Just value."

---

### Footer

- citEther logo (small)
- Links: How it works · Follow Me Power · Community · About
- "Built at Watt The Hack 2026" badge
- Social icons (placeholder)

---

## Animation & Interaction Summary

| Element | Animation | Trigger |
|---------|-----------|---------|
| Hero particles | Continuous drift + mouse parallax | On load |
| Stat counters | Tick up from 0 | On load / scroll into view |
| Step cards | Fade-up + slide-in, staggered 200ms | Scroll into view |
| Follow Me Power map | EV drives route, prices appear | Scroll into view, loops |
| Feature cards | Lift + shadow on hover | Mouse hover |
| Testimonials | Cross-fade cycle, 4s interval | Continuous |
| Section transitions | Wave/diagonal SVG dividers | Between sections |
| CTA buttons | Soft glow pulse | Continuous subtle |
| Demand circles | Scale breathe (1.0→1.1→1.0) | Continuous |

## Responsive Notes

- Mobile: single column, stacked. Map visualisation becomes a simplified vertical timeline instead of side-by-side. Particle network reduces density for performance.
- All animations respect `prefers-reduced-motion`.
- Touch targets minimum 44px.

## Demo Video Walkthrough (for Remotion capture)

The website demo should be captured as a screen recording scrolling through the site, pausing at each section. The Remotion video will overlay narration and highlight key moments:

1. Hero loads → particle network animates → stats tick up (3s)
2. Scroll to Problem → value-leaking animation plays (3s)
3. Scroll to How It Works → steps appear one by one (4s)
4. Scroll to Follow Me Power → EV drives, prices appear (5s) — pause here, this is the money shot
5. Scroll to Community → cards hover-lift (2s)
6. Scroll to CTA → "borrow a cup of power" lands (2s)

Total: ~20 seconds of captured website demo footage for the Remotion video.
