# Dynamic Hero Panel

## Problem

The hero box at the top of the energy dashboard (`panel-price`) is a static price snapshot — spot price, demand, forecast, 24h range. It's the most prominent visual real estate on the screen, but it only tells one story regardless of what the user is investigating.

Two gaps:

1. **Immediate:** Grid inertia just shipped (sync fraction, RoCoF, contingency state) but these numbers are buried in a panel below the fold. The headline grid-stability metric should surface in the hero box when grid stability is the topic.

2. **Bigger picture:** The agent (Ray) has a chat panel on the right side of the dashboard. When a user asks Ray about prices, the hero should show price context. When they ask about grid stability, it should show inertia. When they ask about carbon, it should show emissions intensity. The hero becomes a living surface that the agent populates based on the current conversation topic.

## Approach

### Component architecture — swappable content modules

The hero box becomes a container with a single active **content module** at a time. Each module is a self-contained HTMX partial with its own data flow and refresh cycle. The container handles transitions between modules; the modules handle their own content.

**Five modules:**

| Module key | Title | Primary metric | Secondary metrics | Data source |
|-----------|-------|---------------|-------------------|-------------|
| `prices` | Market Snapshot | Spot price ($/MWh) with colour band | Demand (MW), forecast direction, 24h range, price band label | `energy_query.current_snapshot()` — existing |
| `grid` | Grid Stability | Sync fraction (%) with state colour | RoCoF (Hz/s), contingency label, sync MW / total MW | `inertia.current_inertia()` — existing |
| `carbon` | Carbon Intensity | Carbon intensity (tCO₂/MWh) with band | Renewables %, fuel mix mini-breakdown, intensity trend | New: `carbon.compute_carbon()` — same derivation pattern as inertia |
| `weather` | Weather & Solar | Solar forecast (GHI W/m²) | Wind forecast, temperature, demand correlation | `weather_query` + `solar_query` — existing |
| `freeform` | (agent-defined) | Agent-authored content | Agent-authored content | Agent-generated via API |

Each module follows the same template structure: one large primary metric with colour coding, a status/trend indicator, and a 3-column secondary metrics strip — matching the existing price panel layout.

**Default module:** `prices` (current behaviour preserved). The hero starts as a price panel on page load; it only changes when the agent sets a different context.

### Agent control API

One new endpoint — the agent sets the active hero module:

```
POST /api/v1/hero/context
Body: {"module": "grid"}
```

Returns: `{"ok": true, "data": {"module": "grid", "previous": "prices"}}`

Valid module keys: `prices`, `grid`, `carbon`, `weather`, `freeform`. Invalid key returns 400. Bearer token auth (same as all API endpoints).

**Freeform module — agent-authored content:**

```
POST /api/v1/hero/context
Body: {
    "module": "freeform",
    "title": "Loy Yang Offline — Carbon Impact",
    "content": "<structured payload, see below>"
}
```

When `module` is `freeform`, the request body includes a `title` (displayed as the hero header), `content` (a JSON object with type discriminator, see content contract below), and an optional `size` hint (`"compact"`, `"medium"`, `"large"` — default `"medium"`). The server stores these in ephemeral state alongside the module key; the hero partial renders accordingly.

This is the creative, agenda-driven module. The agent has full control over what appears — data visualisations, conceptual diagrams, annotated schematics, flow diagrams, comparison tables, scenario analyses. It's a whiteboard the agent can draw on in real time during a conversation.

**Content contract — three render paths:**

The freeform module supports three content types, all text-authored by the agent. The `content` field in the API payload is a JSON object with a `type` discriminator:

**1. Mermaid diagrams** — for conceptual/diagrammatic thinking.

```json
{
    "type": "mermaid",
    "diagram": "graph LR\n  A[Heywood trips] --> B[SA loses import]\n  B --> C[SA price $103→$310]"
}
```

Mermaid.js renders the diagram client-side from the text DSL. Covers the full NEM conceptual vocabulary:
- **Failure cascades** (flowchart) — "Heywood trips → SA loses import → price spike → frequency event → FCAS → RoCoF breach → load shed"
- **Interconnector topology** (graph) — VIC1 with five corridors, flow direction and magnitude annotated
- **LOR escalation** (state diagram) — LOR1 → LOR2 (RERT) → LOR3 (load shed)
- **Merit order / generation stack** — conceptual stacking diagrams

This is the primary diagrammatic renderer. The agent writes it natively (text DSL, no pixel-pushing) and it renders as a clean vector diagram. Structurally safer than raw SVG — Mermaid is a constrained grammar, not an arbitrary markup surface.

**2. Chart.js config** — for data visualisations.

```json
{
    "type": "chart",
    "chart_type": "bar",
    "config": { "labels": [...], "datasets": [...], "options": {...} }
}
```

The partial renders a `<canvas>` and initialises Chart.js with the provided config. The library is already vendored. Supports bar, line, doughnut, stacked bar — all the data viz patterns the agent needs for scenario comparisons, trend overlays, and before/after analysis.

**3. Structured HTML** — for metrics, tables, and annotated text.

```json
{
    "type": "html",
    "body": "<div class=\"grid grid-cols-3 gap-4\">..."
}
```

Sanitised HTML using Tailwind utility classes and CityLab custom classes. For metric cards, comparison layouts, callout boxes, and explanatory text with highlighted values. The server sanitises the HTML through an allowlist of tags and attributes before storing — permitted: `div`, `span`, `p`, `table`, `tr`, `td`, `th`, `thead`, `tbody`, `h3`, `h4`, `strong`, `em`, `br`. Permitted attributes: `class`, `style` (with property allowlist: colour, background, padding, margin, font-size, font-weight, text-align, display, grid-*, flex-*, gap, border, border-radius, width, max-width). All other tags/attributes stripped.

**Rendering:** The freeform partial reads the `type` field and renders the appropriate wrapper:
- `mermaid` → `<div class="mermaid">{{ diagram }}</div>` + Mermaid.js init script
- `chart` → `<canvas>` + Chart.js init with the config
- `html` → sanitised body injected as innerHTML

The content inherits the hero panel's CSS context (card padding, font stack, colour variables). The agent is responsible for producing content that fits the hero panel dimensions — roughly 800×200px in the two-thirds dashboard column. Mermaid diagrams auto-scale to container width.

**Dependency:** Mermaid.js (~1 MB minified) needs to be vendored into `static/vendor/`. Load lazily — only when the freeform module is active, not on every page load.

**Data-grounding rules:**
- **Quantitative content** (Chart.js, metrics in structured HTML): all numbers must come from CityLab API data, derived metrics, or scenario-engine output. Scenario output must be visually labelled "Modelled" and use a distinct colour scheme from live data.
- **Conceptual diagrams** (Mermaid): may be drawn freely for explanatory purposes, but must be structurally accurate to NEM topology and mechanics. Don't draw interconnectors landing in wrong regions, don't show VIC islanding like SA can. A topology diagram that's electrically wrong is the diagram-equivalent of a hallucinated price.

**Lifecycle:** Freeform content is ephemeral — it persists in server memory until replaced by another hero context call (freeform or otherwise). No database storage. Switching to any other module (`prices`, `grid`, etc.) clears the freeform content. Switching back to `freeform` without new content shows a placeholder ("No custom content — ask Ray a question").

**How it reaches the browser:** The hero container polls for context changes via a lightweight HTMX endpoint:

```
GET /energy/hero/active
```

Returns the current module key. The hero container uses `hx-get` with a 5-second poll to check for context changes. When the module key changes, it swaps in the new partial. This avoids WebSockets or SSE — pure HTMX, consistent with the rest of the dashboard.

**Server-side state:** Current hero module stored in a simple in-memory variable on the Flask app (or Redis if available). No database table — this is ephemeral session state. Default is `prices`. Resets on server restart.

**Flow:**

1. User asks Ray about grid stability
2. Ray calls `POST /api/v1/hero/context {"module": "grid"}`
3. Next hero poll (≤5s) picks up the change
4. Hero container swaps `partial_hero_prices` → `partial_hero_grid` with a CSS transition
5. User sees inertia metrics in the hero box

### Carbon intensity module (new derivation)

Same pattern as inertia — derive from existing generation mix, no new data source, no migration.

**New service: `src/citylab/services/carbon.py`**

```python
EMISSION_FACTORS = {
    "brown_coal": 1.25,
    "black_coal": 0.90,
    "gas_ccgt": 0.55, "gas_ocgt": 0.55, "gas_recip": 0.55, "gas_steam": 0.55,
    "distillate": 0.95,
    "hydro": 0, "wind": 0, "solar_utility": 0, "solar_rooftop": 0,
    "battery_discharging": 0, "battery_charging": 0, "biomass": 0,
}
```

Functions:
- `compute_carbon(generation_rows) -> dict` — returns `{carbon_intensity_tco2_mwh, renewables_pct, fossil_pct, fuel_breakdown: [{fuel, mw, pct}], intensity_band}`. Exclude `battery_charging` from both numerator and denominator — it's load, not generation; including it as 0-EF generation dilutes the intensity figure artificially. Same exclusion applies to the renewables-% denominator
- `carbon_timeseries(region, dt_from, dt_to, interval) -> list[dict]` — same pattern as `inertia_timeseries`
- `current_carbon(region) -> dict` — convenience wrapper

Intensity bands:
| Band | tCO₂/MWh | Meaning |
|------|----------|---------|
| Very Low | < 0.2 | Mostly renewables |
| Low | 0.2–0.4 | High renewables + some gas |
| Moderate | 0.4–0.7 | Mixed fossil/renewable |
| High | 0.7–1.0 | Coal-dominated |
| Very High | > 1.0 | Heavy brown coal |

API endpoints (same pattern as inertia):
- `GET /api/v1/energy/carbon?region=VIC1&range=24h&interval=1h`
- `GET /api/v1/energy/carbon/current?region=VIC1`

### Price bands (extend existing price module)

Add analytical price band classification to the price view model:

| Band | $/MWh | Label |
|------|-------|-------|
| Negative | < $0 | Solar oversupply |
| Low | $0–$30 | Renewable surplus |
| Normal | $30–$150 | Standard operation |
| Elevated | $150–$300 | Gas peaker territory |
| Stress | $300–$20,300 | Grid stress event |
| MPC | $20,300 | Market Price Cap (FY2025-26) |

These bands are already implicitly used in the price colour coding (`price-low`, `price-amber`, etc.) — this formalises them and adds the label to the hero display.

**Note:** MPC is CPI-indexed annually by AEMC (updates each 1 July). Store as a named constant with the FY noted so next indexation is a one-line change: `MARKET_PRICE_CAP_MWH = 20300.0  # FY2025-26, AEMC indexed`.

### Dashboard changes

**Hero container replacement:**

Replace the current `panel-price` div with a hero container that manages module swapping:

```html
<div id="hero-panel" class="card mb-4 !border-2 !border-volt-300"
     style="background: linear-gradient(180deg, rgba(124,58,237,0.06) 0%, white 100%);">
    <div id="hero-content"
         hx-get="/energy/hero/partial"
         hx-trigger="load, every 5s"
         hx-swap="innerHTML transition:true">
        Loading...
    </div>
</div>
```

The `/energy/hero/partial` endpoint reads the current active module and renders the corresponding partial. Module-specific data refresh (30s for prices/grid, 120s for weather) is handled inside each partial's own HTMX triggers.

**Module tab strip (optional, stretch):** A small row of clickable module icons below the hero for manual switching (user-initiated, not just agent-driven). Each icon calls the same `POST /api/v1/hero/context` endpoint.

### Dynamic sizing

The hero container must expand and contract based on the active content module. Headline metric modules (prices, grid, carbon, weather) are compact (~120–200px tall). Freeform modules with Mermaid diagrams or Chart.js visualisations need significantly more space (400–600px+). The hero must accommodate both gracefully — no clipping, no overflow, no fixed height.

**Implementation:** The hero container uses `height: auto` — it sizes to its content naturally. A `max-height` CSS transition (300ms ease) smooths the expansion/contraction when modules swap. Each module partial sets a size-hint class on its root element:

| Size class | Approx height | Used by |
|-----------|--------------|---------|
| `hero-compact` | 120–200px | prices, grid, carbon, weather |
| `hero-medium` | 300–400px | freeform with Chart.js or simple Mermaid |
| `hero-large` | 500–700px | freeform with complex Mermaid diagrams or multi-section layouts |

The size class is informational for CSS (e.g. setting `min-height` to prevent layout jank during transition) — the container always grows to fit content. No `overflow: hidden` on the hero container.

For freeform content, the agent can optionally include a `size` field (`"compact"`, `"medium"`, `"large"`) in the content payload to hint the appropriate class. Default is `"medium"` if omitted.

**Mermaid auto-scaling:** Mermaid diagrams render as SVG and auto-scale to container width. Vertical height is determined by diagram complexity — the container must not constrain it. The `mermaid` div uses `width: 100%; height: auto; overflow: visible`.

### Transitions

CSS transition on module swap — two properties animated:

```css
#hero-content {
    transition: opacity 150ms ease, max-height 300ms ease;
}
```

The crossfade (opacity) handles the content change; the `max-height` transition smooths the size change so the panels below the hero don't jump. HTMX `transition:true` on the swap handles the crossfade natively; the `max-height` transition is CSS-only and composites with it.

### Agent integration (Ray's side)

Ray needs a tool or instruction to call the hero context endpoint when the conversation topic changes. This is a prompt-level instruction, not a code change to Ray — Ray already has Bearer token access to the CityLab API.

Add to Ray's operational context: "When the user asks about grid stability/inertia, call `POST /api/v1/hero/context {"module": "grid"}`. When they ask about prices/market, set `prices`. When they ask about carbon/emissions/renewables, set `carbon`. When they ask about weather/solar/wind, set `weather`. When the question is unusual, creative, or scenario-based — compose a freeform module with `{"module": "freeform", "title": "...", "content": "..."}` using inline SVG, Chart.js, or structured metrics."

The agent doesn't need to know about the partials or the polling — it just sets the context key and the dashboard responds.

**Data-grounding rule for freeform:** All numbers rendered in freeform content must come from CityLab API data, derived metrics (inertia, carbon), or clearly-labelled scenario-engine output. The agent composes the *presentation*; the *numbers* come from the engine. No fabricated figures rendered as charts — a polished visual with invented data is more misleading than wrong text. Scenario output must be visually distinguished from live data (e.g. different colour scheme, "Modelled" label).

## Scope boundary

**In:** Hero container with module swapping, five content modules (prices, grid, carbon, weather, freeform), agent context API endpoint, carbon intensity service, price band labels, freeform content storage and rendering, CSS crossfade transition, HTMX polling for context changes.

**Out:** WebSocket/SSE push (HTMX polling is sufficient for 5s latency), persistent hero state across sessions (ephemeral is fine), module tab strip for manual switching (stretch goal, not required), content sanitisation layer (agent is a trusted author via Bearer token — no user-supplied content reaches this pathway).

**Deferred:** Module tab strip UI, hero state persistence in database, content sanitisation for untrusted authors (not needed while the only author is the authenticated agent).

## Prerequisite

The inertia calibration fix (sync-fraction-driven state classification) must land before the grid module goes into the hero box. "Watch at 77% synchronous" in the most prominent panel on the screen is worse than not having it.

## Done When

- [ ] Hero container replaces static price panel with module-swappable architecture
- [ ] `prices` module renders identically to current price panel (no regression)
- [ ] `grid` module shows sync fraction, RoCoF, contingency state, MW breakdown
- [ ] `carbon` module shows carbon intensity, renewables %, fuel breakdown, intensity band
- [ ] `weather` module shows solar forecast, wind forecast, temperature, demand correlation
- [ ] `POST /api/v1/hero/context` sets the active module; returns previous
- [ ] `POST /api/v1/hero/context` with `module: "freeform"` accepts `title` and `content`, stores in ephemeral state
- [ ] Freeform partial renders three content types: Mermaid diagrams, Chart.js configs, sanitised structured HTML
- [ ] Mermaid.js vendored and lazy-loaded (only when freeform module is active)
- [ ] Freeform content clears when switching to another module; placeholder shown if no content set
- [ ] Hero container dynamically sizes to content — compact for metric modules, expanded for diagrams/charts
- [ ] Size transitions are smooth (max-height 300ms) — panels below the hero don't jump
- [ ] Hero polls and swaps modules within 5 seconds of context change
- [ ] CSS crossfade transition on module swap (150ms, no jarring pop)
- [ ] `carbon.py` service derives intensity from generation mix with correct EF mapping
- [ ] Carbon API endpoints return timeseries and current snapshot
- [ ] Default module is `prices` on page load (preserves existing behaviour)
- [ ] Agent (Ray) can set hero context via API and the dashboard responds
- [ ] HTML sanitisation allowlist strips non-permitted tags/attributes from structured HTML content
- [ ] Tests cover: carbon derivation, hero context API, module key validation, freeform content storage/retrieval, HTML sanitisation

## Demo Script

1. Open the energy dashboard — hero box shows the familiar price snapshot (default)
2. Start Ray in the agent panel, ask "What's the grid stability looking like?"
3. Watch the hero crossfade from prices to **Grid Stability** — sync fraction, RoCoF, contingency state appear in the headline position
4. Ask Ray "How clean is the grid right now?"
5. Hero crossfades to **Carbon Intensity** — shows tCO₂/MWh, renewables percentage, fuel breakdown
6. Ask Ray "What's the price doing?"
7. Hero crossfades back to **Market Snapshot** — now with explicit price band labels (e.g. "Low — renewable surplus")
8. Ask Ray "What would happen to carbon intensity if Loy Yang went offline?"
9. Hero crossfades to a **freeform module** — Ray has composed a Mermaid diagram showing the failure cascade (Loy Yang trips → 2,200 MW brown coal lost → merit order backfills with gas + imports → carbon intensity delta), labelled "Modelled"
10. Ask Ray "Show me the interconnector topology" — hero swaps to a new freeform with a Mermaid graph showing VIC1's five corridors with current flow magnitudes annotated
11. The key insight: **the agent doesn't just answer questions — it reconfigures the instruments to match your focus, and when the question is novel, it draws the answer on a whiteboard in real time**
