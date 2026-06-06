# citEther — Base44 Update: Three-Way Energy Triangle

Feed this into the running Base44 instances as a content update.

---

## What to add: The Energy Triangle

citEther manages energy flow in three directions between three endpoints. The website currently only shows one scenario. It needs to show all three legs of the triangle:

```
         HOME
        ↗    ↘
      ↙        ↘
   MOBILE ←———→ GRID
  (EV, job site,
   business, tools)
```

### The three flows:

**1. Home ↔ Grid**
- Home solar exports to the grid when prices are high
- Grid charges the home battery when prices are cheap (overnight, midday surplus)
- The Auto-Arb engine handles this automatically

**2. Home ↔ Anywhere (via the grid, not a physical cable)**
- Home solar fills the home battery. Meanwhile, energy is consumed somewhere else entirely — an EV parked across town, a job site, a place of business
- A tradie runs their air compressor and power tools on a construction site — drawing power that's offset by their home solar generation and battery credits through citEther
- An EV plugged in at a shopping centre feeds the grid at that node's rate — the earnings credit back to the household's citEther account
- This is NOT a physical connection between locations. The grid is the wire. citEther is the settlement layer. Your home produces. Your car, your tools, your business consume — wherever they are. One account reconciles it all.
- The concept generalises beyond EVs: any grid-connected consumption point linked to your citEther account benefits from your home generation. The car is the most obvious mobile asset, but it's not the only one.

**3. Car ↔ Grid (Follow Me Power)**
- EV plugged in anywhere feeds power to the grid at that location's node price
- Grid charges the EV when parked at a cheap-rate location
- The car is a mobile battery that earns money wherever it connects

### How to present this visually:

**Add a new section or update the "How It Works" section** with an animated energy triangle diagram:

- Three nodes arranged in a triangle: HOME (top), CAR (bottom-left), GRID (bottom-right)
- Each node has an icon: house with solar panels, EV, power lines/substation
- Animated energy flow lines between all three pairs, flowing in both directions
- The lines pulse with colour to show which direction energy is moving at any moment
- A scenario ticker cycles through real situations:
  - "10am — Solar fills your home battery" (Home generation, animated)
  - "11am — A tradie's compressor runs on a job site in Footscray — offset by their home solar credits" (Home→Remote via settlement, animated)
  - "2pm — Your EV feeds the grid at Springvale at $80/hr" (Mobile→Grid, animated)
  - "6pm — Your home battery covers the evening peak. Your EV credits offset the cost." (Home + settlement, animated)
  - "11pm — Grid recharges everything at overnight rates" (Grid→Home, animated)

### Day-in-the-life narrative:

Add this as supporting copy near the triangle:

"6am: Your battery topped up overnight at $0.08/kWh. 9am: Your solar starts filling your home battery. 11am: You're on a job site in Footscray running power tools — the energy comes from the grid, but your home solar credits offset the cost. 2pm: Your EV is parked at Springvale feeding the grid at $80/hr while you work. 6pm: At home, your battery covers the evening peak. Credits from your car and your home generation offset everything. 11pm: The grid recharges at overnight rates. You earned $47 today across three locations. You didn't touch the app once."

### Key message:

"citEther sees your home, your car, and the grid as one connected energy system — even when they're in different locations. Your home earns from its battery. Your car earns from wherever it's parked. The grid is the wire. citEther is the settlement layer. One account, multiple locations, every flow optimised."
