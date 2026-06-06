# citEther — Base44 PWA App Demo Prompt

## What to build

A responsive PWA-style web application that demonstrates the citEther consumer experience. This is NOT a marketing page — it's the product itself. What a citEther user sees when they open the app on their phone.

**IMPORTANT: This will be viewed in a web browser but must look like it's running on a phone.** Render the entire UI inside a phone frame/bezel (iPhone-style rounded rectangle with notch/dynamic island, status bar showing time/battery/signal). The phone frame should be centered on the page with a dark background behind it. When viewed on desktop, it looks like a phone sitting on a table. On mobile, the frame fills the viewport naturally.

**Design as a native-feeling mobile app** — bottom tab navigation, card-based UI, pull-to-refresh feel, smooth transitions between views. Think of how Uber, Revolut, or the Tesla app feels on mobile. This should look and feel like a real product running on someone's phone, not a website.

---

## Brand

**Name:** citEther (lowercase c-i-t, capital E)
**Logo:** Hashtag/grid geometric mark
**Fonts:** Inter for UI text, JetBrains Mono for numbers/data/prices
**Colours:**
- Primary: Violet #7C3AED
- Secondary: Teal #0D9488
- Positive/earnings: Green #16A34A
- Warning: Amber #D97706
- Dark background: #09090B
- Card surface: #18181B (dark mode) or #FFFFFF (light mode)
- Text primary: #FAFAFA (dark) or #09090B (light)
- Text secondary: #A1A1AA

**Mode:** Dark mode default (energy app, used at night checking earnings)

---

## App Structure (Bottom Tab Navigation)

Five tabs at the bottom of the screen:

### Tab 1: HOME (default view)

The dashboard. What you see when you open the app.

**Top bar:**
- citEther hashtag logo (24px) + "citEther" text
- Notification bell icon (top right, with badge count)
- Profile avatar (top right)

**Hero card: Today's Earnings**
- Large number: "$47.20" (JetBrains Mono, 48px, green)
- Label: "Earned today" (Inter 12px, secondary text)
- Subtext: "↑ $12.40 more than yesterday" (green, with up arrow)
- Badge below: "FiT would've paid you $3.80 · citEther earned you $47.20" (subtle, secondary text — shows the FiT comparison)
- Small sparkline chart showing earnings over the past 7 days
- Tap to expand to detailed earnings breakdown

**Energy Transfer card (TIER 1 — prominent, directly below earnings):**
This is the hero visualization on the home screen. Shows energy flowing from Point A to Point B in real time. This is the single most important UI element — it IS Follow Me Power made visible.

- Full-width card with violet accent border (top edge glow)
- **Visual:** An animated A → B flow diagram on a subtle map background
  - Left pin (Point A): "Your Home — Preston" — house + solar icon, "4.2 kW generating" with a pulsing green dot
  - Animated energy flow line connecting A to B — glowing violet dashes moving left to right, pulsing with flow intensity (thicker line = more kW flowing, thinner = less). The line represents electrons travelling through the grid
  - Small label on the flow line: "via the grid · $0.08/kWh network" (subtle, secondary text — shows network cost transparently)
  - Right pin (Point B): shows the CURRENT active destination — dynamically switches based on what's active:
    - "Mum's flat · Northcote" (home with heart icon) — "1.8 kW flowing · saving $0.15/kWh vs retail"
    - "Job site · Footscray" (tools icon) — "Powering your tools · saving $0.35/kWh vs diesel"
    - "Your EV · Springvale" (car icon) — "Charging · saving $0.55/kWh vs fast charger"
    - "Food bank · Preston" (heart icon) — "Donated 2.4 kWh today"
  - If multiple destinations are active, show the primary one with a small badge: "+2 more active"

- **Live transfer stats (below the map visual):**
  - "Transferring now: 1.8 kW → Mum's flat"
  - "Cost breakdown: $0.06 generation + $0.08 network + $0.03 citEther = $0.17/kWh"
  - "Mum would pay: $0.32/kWh retail — **you save her $0.15/kWh**"
  - "Today: 14.2 kWh transferred · $2.13 saved"

- **Tap to expand — Transfer history (scrollable list):**
  - "This morning: 6.8 kWh → Job site (Footscray)" — saved $3.40 vs diesel
  - "Yesterday: 22.1 kWh → Mum's flat (Northcote)" — saved $3.32 vs retail
  - "Tuesday: 31.4 kWh → EV charge (Springvale)" — saved $14.70 vs fast charger
  - "Monday: 8.2 kWh → Shop (Fitzroy)" — saved $1.48 vs retail

- **Monthly summary badge at bottom of expanded view:**
  - "June: 847 kWh transferred across 4 locations"
  - "Total saved: $127.40"
  - "Network fees paid: $67.80" (honesty — shows we're not hiding the grid cost)

- **The concept in one line beneath the card:** "The grid is the wire. citEther is the settlement."

**My Assets strip (horizontal scrolling cards):**
Each asset is a compact card showing its current state:

Card 1: Solar
- Icon: sun
- "4.2 kW generating"
- Small bar showing current output vs capacity
- Status dot: green (active)

Card 2: Home Battery
- Icon: battery
- "78% · 7.8 kWh"
- SoC bar (violet fill)
- Status: "Discharging → Grid" (with animated arrow)

Card 3: EV
- Icon: car
- "Parked at Springvale"
- "Earning $80/hr via Follow Me Power"
- Status dot: green (active, earning)

Card 4: HVAC
- Icon: thermometer/snowflake
- "Pre-cooled · Coasting"
- "Next cycle: 4:30pm"
- Status: "Smart mode"

Card 5: Hot Water
- Icon: water droplet
- "Heated · 62°C"
- "Solar heated at 11am"
- Status: idle

**Follow Me Power card:**
- Map thumbnail showing current EV location with price badge
- "Your EV is earning $80/hr at Springvale"
- "Tap to see nearby earning opportunities"
- Violet accent border

**Grid Status card:**
- Current wholesale price: "$87.42/MWh" (with price state colour)
- Price direction: "↑ Rising — peak expected 6:30pm"
- Auto-Arb status: "Holding battery for peak discharge"
- Next action: "Discharge at ~$150/MWh (est. 6:15pm)"

**Community card:**
- "Your street: Maple Ave Pod"
- "Pod rank: #3 of 12 streets in your zone"
- "Your contribution: 12% of pod output today"
- Tap to see pod leaderboard

---

### Tab 2: FOLLOW ME POWER

The hero feature gets its own tab.

**Map view (full screen minus tabs):**
- Interactive map centered on Melbourne suburbs
- User's EV shown as a violet pulsing dot at current location
- Nearby grid nodes shown as circles with price badges:
  - Dandenong: "$50/hr" (medium demand, amber circle)
  - Springvale: "$80/hr" (high demand, violet circle, pulsing)
  - Caulfield: "$42/hr" (low demand, grey circle)
  - CBD: "$67/hr" (medium-high, teal circle)
- Demand intensity shown by circle size and colour
- Tap a node to see: current rate, demand level, estimated earnings for 1hr/2hr/4hr connection, distance from current location

**Bottom sheet (draggable up):**
- "Currently earning: $80/hr at Springvale" (header)
- Connected since: "2:15pm (1hr 45min)"
- Earned this session: "$140.00"
- Battery drain: "12 kWh used (EV: 82% → 70%)"
- "End session" button (secondary)

**When EV is not connected:**
- Map shows nearby earning opportunities
- "Best opportunity: Springvale — $80/hr, 8 min drive"
- "Navigate" button (opens maps app)
- Recent sessions list: dates, locations, earnings

**Follow Me Power scenarios (scrollable horizontal cards below map):**

**Tier 1 — featured prominently:**

Card: "Power your job site"
- Icon: wrench/tools
- "2.4M tradies in Australia. Your home solar powers compressors and tools across town."
- "Save $15–25/day on site power"

Card: "Power your parent's flat"
- Icon: home with heart
- "Your rooftop solar offsets your mum's electricity at her unit across town. She didn't install solar. She doesn't need to."
- "I power my mum's flat from my roof."

Card: "EV road trip"
- Icon: car + sun
- "Drive to the coast. Charge at a public charger. Your home solar credits offset the $0.50–0.80/kWh cost. Holiday charging drops to near-zero."

Card: "Earn while you work"
- Icon: hospital/building + EV
- "Park your EV at the hospital for a 12-hour shift. Your car supplies the constrained node. You earn $40–60 while you work."

**Tier 2 — secondary row:**

Card: "Kids at uni"
- Icon: graduation cap
- "Parents' solar subsidises the student's apartment power at a different address. No physical connection needed."

Card: "Holiday house"
- Icon: beach umbrella
- "Beach house draws against your city home's solar. Two properties, one energy account."

Card: "Small business"
- Icon: shop front
- "Shop in Footscray, home in Preston. Home solar offsets your business electricity."

Card: "Donate to a charity"
- Icon: heart + lightning bolt
- "Surplus credits you don't need? Donate them to a food bank, shelter, or sporting club. Charitable energy, tax-deductible."

Card: "Sell to business"
- Icon: handshake
- "Local businesses bid on your community's energy at $0.15–0.20/kWh. Better than FiT for you, cheaper than retail for them."

Card: "Sell to the grid"
- Icon: grid/tower
- "Nobody local needs it? Your Pod fleet sells directly into the wholesale market. FCAS pays $100–300/MWh during grid stress. You become grid infrastructure."

---

### Tab 3: EARNINGS

Financial view. What you've earned and how.

**Period selector:** Today / This Week / This Month / All Time (pill tabs)

**Total earnings hero:**
- "$216.00 this month" (large, green)
- "↑ 18% vs last month"

**Earnings breakdown (vertical list of cards):**

1. "Home battery arbitrage — $165.00"
   - "$3–8/day · avg margin $5.50/day"
   - Sparkline of daily earnings

2. "Follow Me Power — $127.00"
   - "14 sessions across 14 locations"
   - Top location: "Springvale (4 sessions, $48)"

3. "Job site offsets — $89.00"
   - "Home solar credits powering tools at work"
   - "Saved $15–25/day vs grid power"

4. "HVAC savings — $52.00"
   - "Pre-cool/coast avoided 38 kWh at peak rates"

5. "Hot water savings — $37.00"
   - "Solar-heated 92% of the time"

**Transaction history (scrollable list):**
Each row: timestamp · source · amount
- "Today 2:15pm · Follow Me Power (Springvale) · +$80.00"
- "Today 11:30am · Battery discharge · +$4.20"
- "Today 6:00am · Grid charge · -$0.84"
- "Yesterday 6:30pm · Peak discharge · +$12.60"

**Community battery section (if they have shares):**
- "Your 5 kWh share"
- "This month: $12.40 earned"
- "Mode: Mixed (60% bill offset, 40% cash)"
- "Change allocation →"

---

### Tab 4: MY POD

Community and social features.

**Pod header:**
- "Maple Ave Pod" (name)
- "14 households · 62 kW solar · 3 EVs · 1 community battery"
- Pod status: "Active · Self-supplied 73% today"

**Leaderboard card:**
- Your position: "#3 of 14"
- Top 5 list with household names (or anonymous "House 7"), contribution %, and earnings
- Your row highlighted in violet
- "You're in the top 25% of your pod" badge

**Social norming comparison:**
- "Similar homes in your area averaged $38/month. You earned $52. Top 15%."
- Bar chart showing your earnings vs pod average vs top performer
- Smiley/neutral/frown indicator based on relative performance

**Pod energy flow (animated):**
- Simple diagram showing energy flowing between pod members
- "House 3's solar → Your battery (2.4 kWh shared today)"
- "Your battery → House 7 (1.1 kWh shared today)"
- Net pod sharing summary

**Grid events:**
- "Next event: Peak demand expected 6:30pm"
- "87% of your pod participated last time"
- "Opt in" button (violet)
- Past events with participation rate and earnings

**Community feed:**
- Tips, shared achievements, local energy news
- "Sarah shared: 'Switched hot water to solar-only — saving $15/month'"
- "Pod milestone: Maple Ave hit 500 kWh shared locally!"

---

### Tab 5: SETTINGS / PROFILE

**Account:**
- Name, email, address
- citEther ID
- Payment details (bank account for cash-outs)

**My assets:**
- List of connected devices with connection status
- "Add new asset" button
- Per-asset settings (SoC floor, comfort preferences)

**Auto-Arb preferences:**
- Comfort floor: "Never below 22°C cooling / 19°C heating" (slider)
- Battery SoC floor: "Never below 20%" (slider)
- "Family mode" toggle: "Ignore price spikes when HVAC is running"
- Dispatch aggressiveness: Conservative / Balanced / Aggressive

**Follow Me Power settings:**
- Auto-connect when plugged in: on/off
- Minimum earning rate: "$30/hr" (slider — don't discharge for less)
- EV SoC floor: "Never discharge below 40%" (slider)

**Community battery:**
- Share allocation: "5 kWh"
- Value mode: Use it / Cash it / Mix (with slider for split)

**Pod membership:**
- Current pod: "Maple Ave Pod"
- Leaderboard visibility: on/off (privacy toggle)
- Grid event auto-opt-in: on/off

**Notifications:**
- Earnings milestones
- Grid events
- Follow Me Power opportunities nearby
- Pod activity

---

## Micro-interactions & Animation

| Element | Animation |
|---------|-----------|
| Earnings counter | Ticks up in real time when actively earning |
| Asset status dots | Pulse when active (generating, discharging, earning) |
| Follow Me Power map nodes | Breathe (scale) based on demand intensity |
| EV dot on map | Gentle pulse at current location |
| Leaderboard position | Slides up/down with position changes |
| Tab transitions | Smooth horizontal slide between views |
| Card taps | Scale down 98% on press, spring back on release |
| Pull to refresh | Custom animation — citEther logo spins |
| Earnings notification | Slide down from top with amount, auto-dismiss after 3s |

## Phone Frame & Responsive Behaviour

**CRITICAL: The entire app renders inside a phone bezel on desktop.**

- **Desktop/tablet view:** A centred iPhone-style device frame (rounded corners, notch/dynamic island, status bar with time/battery/signal). Dark background (#09090B) behind the phone. The phone frame is ~375px wide, ~812px tall (iPhone X proportions). The app renders INSIDE this frame. It should look like a screenshot of a real app running on a real phone.
- **Mobile view:** The frame is hidden — the app fills the viewport naturally and looks native.
- The phone frame is purely cosmetic — do not restrict touch/scroll behaviour.

## Demo Data

Pre-populate with realistic, grounded demo data:
- User: "Alex" (gender-neutral)
- Location: Melbourne eastern suburbs (Glen Waverley)
- Assets: 6.6 kW solar, 10 kWh battery (Tesla Powerwall), EV (65 kWh, currently parked at Springvale)
- Pod: "Maple Ave Pod" — 14 households

**Earnings (realistic, defensible):**
- Monthly total: ~$216
- Breakdown: Home battery arbitrage $3–8/day (~$165/month), Follow Me Power EV sessions $4–12/hr (~$127 from 14 locations this month), job site offsets $15–25/day (~$89 cumulative)
- Follow Me Power sessions: 14 this month across different locations
- Pod rank: #3 of 14

**Map node rates (grounded in distribution constraint differentials):**
- Dandenong: $50/hr
- Springvale: $80/hr (high constraint)
- CBD: $35/hr (low constraint)
- Geelong: $62/hr
- Caulfield: $42/hr

**Real-time energy flow labels:**
- "Home → Grid: 2.1 kW exporting"
- "EV ← Grid: 7.4 kW charging (Springvale node, $0.38/kWh credit)"
- "Account: Home generated 420 kWh this month"
