# citEther — Base44 Update: Energy Transfer

Paste this into your existing citEther app build to add the new features.

---

## UPDATE INSTRUCTIONS

Add the following new features to the existing app. Do not remove or replace existing functionality — these are additions.

---

## 1. ENERGY TRANSFER CARD — Home Screen (Tier 1 Hero Element)

Add a new full-width card to the home/dashboard screen, positioned directly below the earnings hero card and ABOVE the assets strip. This is the most important new element — it visualises the core concept of Follow Me Power: energy flowing from Point A to Point B through the grid.

**Layout:**
- Full-width card with a violet (#7C3AED) accent glow on the top edge
- Subtle map background (low-opacity street map of Melbourne suburbs)

**The A → B visualization:**
- Left side: a pin/circle labelled **"Your Home — Preston"** with a house + solar panel icon. Below it: "4.2 kW generating" with a pulsing green status dot
- Right side: a pin/circle showing the **current active destination** (see list below). The destination changes dynamically
- Connecting them: an **animated flow line** — glowing violet (#7C3AED) dashes that move from left to right, representing energy flowing through the grid. The line should pulse — thicker when more kW is flowing, thinner when less. This animation is the centrepiece
- Small label on the flow line: "via the grid · $0.08/kWh network"

**Active destinations (the right-side pin cycles between these, or shows whichever is currently active):**
1. "Mum's flat · Northcote" — home with heart icon — "1.8 kW flowing · saving $0.15/kWh vs retail"
2. "Job site · Footscray" — wrench/tools icon — "Powering your tools · saving $0.35/kWh vs diesel"
3. "Your EV · Springvale" — car icon — "Charging · saving $0.55/kWh vs fast charger"
4. "Food bank · Preston" — heart + lightning icon — "Donated 2.4 kWh today"

If multiple destinations are active simultaneously, show the primary one and add a small badge: "+2 more active"

**Stats below the visualization:**
- "Transferring now: 1.8 kW → Mum's flat"
- "Cost: $0.06 generation + $0.08 network + $0.03 citEther = **$0.17/kWh**"
- "Mum would pay: $0.32/kWh retail — **you save her $0.15/kWh**"
- "Today: 14.2 kWh transferred · $2.13 saved"

**Tap to expand — shows transfer history:**
- "This morning: 6.8 kWh → Job site (Footscray)" — saved $3.40 vs diesel
- "Yesterday: 22.1 kWh → Mum's flat (Northcote)" — saved $3.32 vs retail
- "Tuesday: 31.4 kWh → EV charge (Springvale)" — saved $14.70 vs fast charger
- "Monday: 8.2 kWh → Shop (Fitzroy)" — saved $1.48 vs retail

**Monthly summary at bottom of expanded view:**
- "June: 847 kWh transferred across 4 locations"
- "Total saved: $127.40"
- "Network fees paid: $67.80"

**One-liner beneath the card:** "The grid is the wire. citEther is the settlement."

---

## 2. FiT COMPARISON BADGE — Earnings Hero Card

On the existing earnings hero card on the home screen, add a subtle comparison line below the daily earnings number:

"FiT would've paid you $3.80 · citEther earned you $47.20"

Use secondary/muted text colour. This makes the value proposition visible every time the user opens the app.

---

## 3. FOLLOW ME POWER SCENARIOS — Add to Follow Me Power Tab

In the Follow Me Power tab (the map view), add scrollable horizontal scenario cards below the map. Two rows:

**Row 1 — Featured scenarios (larger cards):**

Card: "Power your job site"
- Icon: wrench/tools
- "Your home solar powers compressors and tools across town."
- "Save $15–25/day on site power"

Card: "Power your parent's flat"
- Icon: home with heart
- "Your rooftop solar offsets your mum's electricity at her unit. She didn't install solar. She doesn't need to."

Card: "EV road trip"
- Icon: car + sun
- "Drive to the coast. Your home solar credits offset $0.50–0.80/kWh charger costs. Holiday charging drops to near-zero."

Card: "Earn while you work"
- Icon: hospital/building + EV
- "Park your EV at work for a 12-hour shift. Your car supplies the local grid node. Earn $40–60 while you work."

**Row 2 — More ways to use Follow Me Power (smaller cards):**

Card: "Kids at uni" — graduation cap icon — "Parents' solar subsidises the student's apartment at a different address."

Card: "Holiday house" — beach umbrella icon — "Beach house draws against your city home's solar. Two properties, one account."

Card: "Small business" — shop front icon — "Shop in Footscray, home in Preston. One energy account."

Card: "Donate to a charity" — heart + lightning icon — "Donate surplus credits to a food bank, shelter, or sporting club. Tax-deductible."

Card: "Sell to business" — handshake icon — "Local businesses bid on your community's energy at $0.15–0.20/kWh. Better than FiT for you, cheaper than retail for them."

Card: "Sell to the grid" — grid/tower icon — "Your Pod sells directly into the wholesale market. FCAS pays $100–300/MWh during grid stress."

---

## 4. EARNINGS TAB UPDATE

Update the earnings breakdown to reflect the Follow Me Power focus:

1. "Home battery arbitrage — $165.00" — "$3–8/day · avg margin $5.50/day"
2. "Follow Me Power — $127.00" — "14 sessions across 14 locations"
3. "Job site offsets — $89.00" — "Home solar credits powering tools at work · saved $15–25/day vs grid power"
4. "HVAC savings — $52.00" — "Pre-cool/coast avoided 38 kWh at peak rates"
5. "Hot water savings — $37.00" — "Solar-heated 92% of the time"

Monthly total: $216.00

Add to transaction history:
- "Today 2:15pm · Transfer to Mum's flat (Northcote) · saved $2.13"
- "Today 9:00am · Transfer to job site (Footscray) · saved $3.40"
- "Today 11:30am · Battery discharge · +$4.20"

---

## DESIGN NOTES

- All new cards use the existing dark mode card style (#18181B surface on #09090B background)
- Violet (#7C3AED) for accent borders and the energy flow animation
- Green (#16A34A) for positive earnings/savings numbers
- JetBrains Mono for all dollar amounts and kWh figures
- Inter for all labels and descriptions
- The energy transfer flow line animation is the single most important visual — make it smooth, continuous, and eye-catching
