---
validation:
  status: valid
  validated_at: '2026-06-05T11:19:57+10:00'
---

## Product Requirements Document (PRD) — Energy Market Charts

**Project:** CityLab
**Scope:** Interactive charting for Victorian energy market data (prices, generation mix, demand)
**Author:** Robbo (Architect)
**Status:** Draft

---

## Executive Summary

CityLab collects real-time Victorian energy market data from OpenElectricity v4 at 5-minute intervals — spot prices, demand, and generation output by fuel type. The current `/energy` dashboard shows point-in-time snapshots (hero price, static generation bars, weather conditions) but provides no way to explore how these values change over time.

This PRD specifies an interactive charting layer that lets users visualise price trends, generation mix composition, and demand curves across configurable time ranges. The charts use the existing Chart.js library (already vendored) and are served by new API endpoints that return chart-ready JSON from the existing query layer.

The goal is a functional baseline — clean, interactive, and accurate — not a polished analytics product. The OpenNEM/OpenElectricity dashboard provides the reference standard for energy market visualisation patterns.

---

## 1. Context & Purpose

### 1.1 Context

The data pipeline now delivers real VIC1 market data: ~1,152 price/demand rows per 4-day window and ~8,064 generation rows (7 fuel types). This data exists in the database but is only surfaced as point-in-time values. Users cannot see trends, correlations, or patterns without charting.

### 1.2 Target User

Hackathon judges and demo audience evaluating CityLab's energy monitoring capability. Secondary: any user wanting to understand Victorian energy market dynamics over time.

### 1.3 Success Moment

A user opens the energy dashboard, selects a 24-hour time range, and immediately sees the price spike at the morning peak, the solar generation ramp driving midday price dips, and the evening demand surge — all in correlated, interactive charts they can hover over for exact values.

---

## 2. Scope

### 2.1 In Scope

- Price time-series chart (line or area) showing $/MWh over time
- Generation mix stacked area chart showing MW output by fuel type over time
- Demand curve overlay (on price chart or standalone)
- Time range selector with presets: 1h, 6h, 24h, 7d, 30d
- Interval aggregation control: 5min (raw), 1h, 1d (where time range makes it sensible)
- Hover tooltips showing exact timestamp and values
- Responsive layout for desktop and tablet viewports
- API endpoints returning chart-ready JSON time-series data
- Integration into the existing `/energy` dashboard page

### 2.2 Out of Scope

- Interconnector flow charts (insufficient real data — only 65 rows; requires AEMO MMS source)
- Cross-region comparison (VIC1 only; multi-region is a future data source expansion)
- Data export or download (CSV, PNG)
- User-saved chart configurations or preferences
- Anomaly detection, alerts, or embedded analytics
- Real-time streaming (HTMX polling at existing intervals is sufficient)
- Generator bid/submission visualisation (no real data source yet)
- Pre-dispatch forecast overlay (insufficient real forecast data)

---

## 3. Success Criteria

### 3.1 Functional Success Criteria

- SC1: User can view VIC1 spot price as a time-series chart for any supported time range
- SC2: User can view generation mix as a stacked area chart showing all fuel types over time
- SC3: User can see demand alongside price to correlate market dynamics
- SC4: Time range selection updates all charts simultaneously
- SC5: Hovering on any chart shows a tooltip with the exact timestamp and value(s)
- SC6: Charts display real data from the database, never synthetic or placeholder data

### 3.2 Non-Functional Success Criteria

- SC7: Charts render within 500ms for up to 30 days of 5-minute data (~8,640 points)
- SC8: Charts are responsive and usable on viewports ≥768px wide
- SC9: Chart colours for fuel types are consistent with the existing generation mix panel

---

## 4. Functional Requirements (FRs)

**FR1: Price Time-Series Chart**
The energy dashboard displays a line or area chart showing VIC1 spot price ($/MWh) over time. The x-axis is time, the y-axis is price. The chart updates when the time range or interval changes.

**FR2: Generation Mix Stacked Area Chart**
The energy dashboard displays a stacked area chart showing generation output (MW) by fuel type over time. Each fuel type (coal, gas, solar, wind, hydro, battery, other) is a distinct coloured layer. The chart updates when the time range or interval changes.

**FR3: Demand Curve**
The energy dashboard displays demand (MW) as a time-series. This can be overlaid on the price chart as a secondary y-axis, or displayed as a separate chart. The demand curve updates with time range and interval changes.

**FR4: Time Range Selector**
The dashboard provides a control to select the time range for all charts. Preset options: 1h, 6h, 24h, 7d, 30d. Selecting a range updates all charts on the page simultaneously. Default range on page load: 24h.

**FR5: Interval Aggregation Control**
The dashboard provides a control to select the data aggregation interval. Options: 5min (raw dispatch intervals), 1h (hourly average), 1d (daily average). The control shows only intervals that make sense for the selected time range (e.g., 5min is not offered for 30d; 1d is not offered for 1h). Default: auto-select based on time range.

**FR6: Chart Tooltips**
Hovering over any data point on any chart shows a tooltip displaying the exact timestamp and value(s) at that point. For the generation stacked area, the tooltip shows all fuel type values and the total.

**FR7: Chart Data API Endpoints**
New API endpoints serve chart-ready JSON time-series data. Endpoints accept time range and interval parameters and return arrays of {timestamp, value} objects (or equivalent). Endpoints serve from the existing query layer (`energy_query.py`). At minimum:
- Price time-series endpoint
- Generation time-series endpoint (grouped by fuel type)
- Demand time-series endpoint

**FR8: Fuel Type Colour Consistency**
Chart colours for fuel types match the existing generation mix panel colours. A single colour mapping is shared between the static panel and the stacked area chart.

**FR9: Chart Layout and Placement**
Charts are placed within the existing `/energy` dashboard page, below or alongside the current snapshot panels. The layout is responsive and does not break the existing dashboard on any supported viewport.

**FR10: Empty State Handling**
When no data exists for the selected time range, charts display a clear empty state message (e.g., "No data available for this range") rather than a blank canvas or error.

---

## 5. Non-Functional Requirements (NFRs)

**NFR1: Performance**
Chart data API endpoints return responses within 200ms for queries spanning up to 30 days of 5-minute data. Client-side chart rendering completes within 300ms for up to 8,640 data points.

**NFR2: Data Point Limit**
For large time ranges at fine intervals, the API applies server-side aggregation or downsampling to keep the data point count below 10,000 per series. The interval auto-selection in FR5 is the primary mechanism for this.

**NFR3: No New Dependencies**
Charts use the existing Chart.js 4.4.1 library (already vendored). No new JavaScript libraries or build tools are introduced.

---

## 6. UI Overview

The charting area sits below the existing snapshot panels (price hero, generation mix, interconnectors, weather) on the `/energy` page.

**Layout (top to bottom):**
1. Existing snapshot panels (unchanged)
2. Time range selector bar + interval control (horizontal, right-aligned or centred)
3. Price + demand chart (full width, ~300px height)
4. Generation mix stacked area chart (full width, ~300px height)

**Interactions:**
- Time range buttons highlight the active selection
- Interval control updates to show valid options for the selected range
- Hovering on a chart shows a vertical crosshair line and tooltip
- Charts share the same x-axis time range so visual correlation is immediate

**Colour palette for fuel types (consistent with existing panel):**
- Coal: use existing colour
- Gas: use existing colour
- Solar: use existing colour
- Wind: use existing colour
- Hydro: use existing colour
- Battery: use existing colour
- Other: use existing colour
