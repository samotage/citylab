---
name: citether-brand
description: citEther brand identity, colour palette, typography, logo assets, and MARP presentation theming. Use this skill when producing any citEther-branded output — presentations, documents, diagrams, UI components, or marketing materials. Provides the token mapping from the otageLabs house MARP theme to citEther's palette so slides render on-brand without a custom CSS file.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(marp *)
  - Bash(ls *)
  - Bash(mkdir -p *)
  - Bash(open *)
version: 1.0.0
---

# citEther Brand

## Brand Identity

**citEther** — a portmanteau of *city* and *ether*. The city is the physical infrastructure: buildings, transmission lines, substations, load centres. The ether is the invisible intelligence that connects, balances, and optimises the grid. citEther sits at the intersection — where physical energy infrastructure meets AI-driven decision-making.

**Positioning:** Energy intelligence platform for the Victorian electricity grid. Precision, convergence, intelligent balance.

**Values:** Precision (clean geometry, no decoration), Convergence (where forces meet), Clarity (understood at a glance), Restraint (subtract until essential).

## The Wordmark

Always styled as **citEther** — lowercase "cit", uppercase "E", lowercase "ther".

In colour contexts:
- **cit** in Amber (`#E8A838`)
- **Ether** in Deep Teal (`#0D7377`)

On dark backgrounds: **cit** in Amber, **Ether** in White.

Monochrome: full word in Charcoal on light, White on dark. Casing always maintained.

Never: "Citether", "CitEther", "CITETHER", "citether".

## The Mark (Tilted Hash)

Two amber diagonal bars intersecting two charcoal horizontal bars. The hash reads as "network" and "grid." The tilt adds energy and forward momentum.

### Logo Files

All at `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/logo/`:

| File | Size | Use |
|------|------|-----|
| `citether-mark.svg` | 1024x1024 | Production vector |
| `citether-mark-responsive.svg` | Scalable | Web `<img>`, CSS background |
| `citether-mark-1024.png` | 1024px | Print, high-res |
| `citether-mark-512.png` | 512px | Hero images |
| `citether-mark-256.png` | 256px | Social, thumbnails |
| `citether-mark-128.png` | 128px | App icons |
| `citether-mark-64.png` | 64px | Navigation, toolbar |
| `citether-mark-32.png` | 32px | Favicon 2x |
| `citether-mark-16.png` | 16px | Favicon |

**Clear space:** width of one bar in the hash around the mark.
**Minimum size:** 32x32 pixels.
**Orientation:** always at the designed tilt angle. Never rotate, skew, or straighten.

## Colour Palette

### Primary

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| **Amber** | `#E8A838` | 232, 168, 56 | Primary accent. Diagonal bars in mark. Energy, warmth. CTAs, highlights, key data. |
| **Charcoal** | `#2D2926` | 45, 41, 38 | Primary dark. Horizontal bars in mark. Infrastructure, stability. Body text, dark backgrounds, headers. |
| **Deep Teal** | `#0D7377` | 13, 115, 119 | The ether — intelligence, data. Secondary accents, interactive elements. |

### Secondary

| Name | Hex | Role |
|------|-----|------|
| **White** | `#FFFFFF` | Backgrounds, clear space |
| **Warm Grey** | `#8A8480` | Secondary text, metadata, borders |

### Extended (Data Visualisation)

| Name | Hex | Role |
|------|-----|------|
| **Amber Light** | `#F5D08A` | Chart fills, hover states |
| **Teal Light** | `#4DA8AB` | Secondary data series, positive indicators |
| **Teal Dark** | `#094F52` | Dark mode accents |
| **Charcoal Light** | `#4A4542` | Subtle borders, dark card backgrounds |
| **Signal Red** | `#D94F4F` | Alerts, negative price events (data states only, never decorative) |
| **Signal Green** | `#4CAF50` | Positive states (data states only, never decorative) |

### Colour Rules

- Amber + Charcoal is the primary brand expression. When only two colours available, use these.
- Deep Teal is the digital accent — does not appear in the mark.
- Never use amber on teal (insufficient contrast). Amber on charcoal or white; teal on charcoal or white.
- Signal colours for data states only.
- Zero violet/purple anywhere.

## Typography

| Weight | Face | Usage |
|--------|------|-------|
| Inter 700 | Bold | Page titles, hero numbers |
| Inter 600 | SemiBold | Section headings, card titles |
| Inter 400 | Regular | Body text, descriptions |
| Inter 300 | Light | Metadata, timestamps |
| JetBrains Mono / SF Mono | Mono | Data values, code, tabular numbers |

**Eyebrow labels:** JetBrains Mono 500, 11px, 0.12em tracking, uppercase.

**Body:** min 14px screen, 10pt print. Line height 1.5x. Max line length 72ch.

## MARP Presentations — citEther Theming

citEther has its own MARP theme at `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/marp/citether.css`. It is a standalone theme adapted from the otageLabs house theme with the full dual-accent palette: Amber for primary accents (stripes, bullets, stats, blockquote borders, strong text) and Deep Teal for secondary accents (h2, h4/eyebrow labels, table headers, links, code tints).

### Option A: Standalone theme (preferred)

Register the citEther theme by passing it to marp-cli:

```bash
marp deck.md --config-file ~/.marprc.yml --theme-set /Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/marp/citether.css
```

Frontmatter:

```markdown
---
marp: true
theme: citether
paginate: true
header: '![w:100](/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/logo/citether-mark-128.png)'
---
```

### Option B: Inline override (fallback)

If the standalone CSS is not available, use the otageLabs theme with inline `<style>` overrides. This maps copper → amber and adds teal as the secondary accent:

```markdown
---
marp: true
theme: otagelabs
paginate: true
header: '![w:100](/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/logo/citether-mark-128.png)'
style: |
  section { font-family: 'Inter', Arial, sans-serif; }
  section::before { background: #E8A838; }
  h1 { border-bottom-color: #E8A838; letter-spacing: -0.03em; }
  h2 { color: #0D7377; }
  h4 { font-family: 'JetBrains Mono', monospace; color: #0D7377; letter-spacing: 0.12em; }
  h5 { font-family: 'JetBrains Mono', monospace; letter-spacing: 0.12em; }
  ul > li::before { color: #E8A838; }
  ol > li::marker { color: #E8A838; }
  thead tr { background: #0D7377; }
  thead th { font-family: 'JetBrains Mono', monospace; }
  tbody td { border-bottom-color: #F5D08A; }
  blockquote { border-left-color: #E8A838; }
  hr { border-top-color: #E8A838; }
  a { color: #0D7377; }
  code { font-family: 'JetBrains Mono', monospace; background: rgba(13,115,119,0.08); }
  pre { border-color: #F5D08A; border-left-color: #E8A838; }
  .label { font-family: 'JetBrains Mono', monospace; color: #0D7377; }
  .stat-hero, .stat-big { font-family: 'JetBrains Mono', monospace; color: #E8A838; }
  .stat-label { font-family: 'JetBrains Mono', monospace; }
  section::after { font-family: 'JetBrains Mono', monospace; }
  section.lead::before { background: #E8A838; }
  section.lead h2 { color: #E8A838; }
  section.lead strong { color: #E8A838; }
  section.lead em { color: #4DA8AB; }
  section.divider::before { background: #E8A838; }
  section.divider h4 { color: #0D7377; }
  section.divider h1 { border-left-color: #E8A838; }
  section.dark h1 { border-bottom-color: #E8A838; }
  section.dark h2 { color: #E8A838; }
  section.dark h4 { color: #0D7377; }
  section.dark strong { color: #E8A838; }
  section.dark em { color: #4DA8AB; }
  section.dark p { color: #D4D0CC; }
  section.dark li { color: #D4D0CC; }
  section.dark ul > li::before { color: #E8A838; }
  section.dark ol > li::marker { color: #E8A838; }
  section.dark blockquote { border-left-color: #E8A838; }
  section.dark a { color: #4DA8AB; }
  section.dark .label { color: #0D7377; }
  section.dark .stat-hero, section.dark .stat-big { color: #E8A838; }
  section.dark thead tr { background: #0D7377; }
  section.dark pre { border-color: rgba(232,168,56,0.4); border-left-color: #E8A838; }
  section.dark hr { border-top-color: rgba(232,168,56,0.5); }
  section.dark table tbody td { border-bottom-color: rgba(232,168,56,0.3); }
  section.dark code { background: rgba(255,255,255,0.08); color: #D4D0CC; }
  ul ul > li::before { color: #F5D08A; }
  section.quote::before { background: #E8A838; }
  section.quote h1 { color: #0D7377; }
  section.quote blockquote::before { color: #E8A838; }
  section.closer::before { background: #E8A838; }
  section.closer > p:last-child { color: #E8A838; }
---
```

### Colour mapping summary (otageLabs → citEther)

| Role | otageLabs | citEther |
|------|-----------|----------|
| Top stripe, bullets, stats, strong, blockquote border | Copper `#C78C5C` | Amber `#E8A838` |
| h2, h4/eyebrows, table headers, labels, links | Copper `#C78C5C` | Deep Teal `#0D7377` |
| Dark slide body text | Copper Mid `#E8D5C4` | Neutral `#D4D0CC` |
| Dark slide links, emphasis | Copper `#C78C5C` | Teal Light `#4DA8AB` |
| Light tones (row borders, nested bullets) | Copper Lt `#F5EDE5` | Amber Lt `#F5D08A` |

### Title Slide

```markdown
<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _header: '' -->

![w:120](/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/logo/citether-mark-256.png)

# Presentation Title

## Subtitle or tagline

### Presenter Name · Date
```

Use `<!-- _header: '' -->` on lead slides to suppress the persistent header logo (lead has its own placement).

### Section Divider

```markdown
<!-- _class: divider -->

#### Section Label

# Section Title

Optional subtitle
```

CSS handles uppercase + letter-spacing on h1. Write normal sentence-case.

### Dark Slide

```markdown
<!-- _class: dark -->
<!-- _header: '![w:100](/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/logo/citether-mark-128.png)' -->

# Slide Title

Body content with amber-tinted text on charcoal.
```

The mark renders well on charcoal backgrounds without modification.

### Quote Slide

```markdown
<!-- _class: quote -->

# Consumer Voice

> "I already have a full time job."
> — Australian solar owner on managing wholesale prices
```

### Stats Slide

```markdown
# Key Metric

<div class="stat-hero">4.3M</div>
<div class="stat-label">Solar households in Australia</div>
```

### Two-Column Layout

```markdown
# Heading spans full width

<div class="columns">

**Left column content**

Explanation or data.

**Right column content**

Complementary detail.

</div>
```

Variants: `columns-33-67`, `columns-67-33`.

### Closer Slide

```markdown
<!-- _class: closer -->

# Next Steps

- Action item one
- Action item two

**citEther · intelligence for the grid**
```

## CLI

citEther theme (standalone):
```bash
marp deck.md --config-file ~/.marprc.yml --theme-set /Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/marp/citether.css          # HTML
marp deck.md --config-file ~/.marprc.yml --theme-set /Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/marp/citether.css --pdf     # PDF
marp deck.md --config-file ~/.marprc.yml --theme-set /Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/marp/citether.css --pptx    # PPTX
```

otageLabs theme with inline overrides (fallback):
```bash
marp deck.md --config-file ~/.marprc.yml                  # HTML
marp deck.md --config-file ~/.marprc.yml --pdf             # PDF
marp deck.md --config-file ~/.marprc.yml --pptx            # PPTX
```

## Brand References

Full brand guidelines: `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/citether-brand-guidelines.md`
Shared content layer: `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/shared-content-layer.md`
Base44 corrective prompt: `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/base44-corrective-prompt.md`
MARP theme CSS: `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/marp/citether.css`
Logo assets: `/Users/samotage/dev/otagelabs/hackathon/citylab/docs/brand/logo/`

## Do / Don't

**Do:** Use the mark at its designed tilt. Maintain clear space. Use responsive SVG for web. Pair amber with charcoal or white. Write "citEther" with correct casing.

**Don't:** Rotate/stretch/distort the mark. Place on amber or teal backgrounds. Use below 32x32. Add shadows/outlines/effects. Rearrange bar colours. Use violet/purple anywhere.

## Design Aesthetic

Monocle magazine meets Bloomberg Terminal. Dense, confident, editorial. Information-rich, not whitespace-padded. Rule lines over card borders. Asymmetric layouts over centred-everything. Tight padding (80-100px), not 200px gaps. Let typography do the work.

**Tagline:** *citEther — intelligence for the grid*
