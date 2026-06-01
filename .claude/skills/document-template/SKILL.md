---
name: document-template
description: Generate branded otageLabs documents (proposals, quotations, technical briefs, evaluation reports, feasibility analyses) as PDF. HTML skeleton with structural classes + otageLabs document CSS + /generate-pdf. Use when asked to produce a client-facing document, proposal, quotation, report, brief, or any long-form deliverable that should carry otageLabs branding.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(ls *)
  - Bash(mkdir -p *)
  - Skill(generate-pdf)
version: 2.0.0
argument-hint: "[source content or .md file] [document-type: proposal|quotation|brief|evaluation|feasibility]"
---

# Document Template

Produce branded otageLabs documents rendered as A4 PDF. Pipeline: author an HTML file using the structural skeleton below, link Maren's `otagelabs-document.css`, render via `/generate-pdf`.

## When to invoke this skill

- The operator requests a proposal, quotation, technical brief, evaluation report, feasibility analysis, or any long-form client-facing document
- The deliverable needs otageLabs branding and will be sent to a client or left behind after a meeting
- A markdown source file exists and needs to be rendered as a branded document

**Not this skill:** slide decks (use `/marp-presentation`), internal notes, README files, or documents that don't need brand treatment.

## Pipeline

```
HTML skeleton (structural classes, content filled in)
  + otagelabs-document.css linked
  → /generate-pdf (file_to_pdf, with Puppeteer config below)
  → branded A4 PDF
```

**Source format is HTML, not markdown.** The document uses structural `<div>` classes (cover, page-header, section-label, flowchart, phase-card, gate) that have no natural markdown syntax. Author the HTML directly using the skeleton below.

**Do NOT:**
- Write inline `<style>` blocks — all styling comes from the linked CSS
- Use markdown-to-HTML converters (pandoc, python-markdown) — they produce generic HTML without the structural classes
- Call `mcp__puppeteer-pdf__*` tools directly — every render goes through `/generate-pdf`

## CSS location

```
/Users/samotage/Documents/01_otagelabs/Foundational/Branding/document/otagelabs-document.css
```

## Logo location

```
file:///Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png
```

Use `file://` prefix in all `<img src="...">` references to the logo. Puppeteer resolves local file paths via this protocol.

## Puppeteer render config

Pass these parameters when invoking `/generate-pdf` with `file_to_pdf`:

| Parameter | Value |
|-----------|-------|
| `format` | `A4` |
| `print_background` | `true` |
| `display_header_footer` | `true` |
| `margin_top` | `22mm` |
| `margin_right` | `25mm` |
| `margin_bottom` | `22mm` |
| `margin_left` | `25mm` |
| `header_template` | `<span></span>` |
| `footer_template` | (see below) |

**Footer template** (copy-paste — inline styles required, Puppeteer ignores `<style>` blocks in header/footer context):

```html
<div style="width:100%;font-family:Arial,sans-serif;font-size:9pt;color:#8A8480;margin:0;padding:0 25mm;"><table style="width:100%;border:none;border-collapse:collapse;font-size:9pt;color:#8A8480;"><tr><td style="text-align:left;border:none;padding:0;">otageLabs &mdash; Confidential</td><td style="text-align:right;border:none;padding:0;">Page <span class="pageNumber"></span></td></tr></table></div>
```

**Header is deliberately empty** (`<span></span>`). The running header with logo is achieved via the `.page-header` div in the document body, not via Puppeteer's header zone. This was a deliberate v2.0 design decision — Puppeteer's header template clips at ~10mm and cannot reliably render logos, backgrounds, or borders.

## HTML skeleton

Copy this skeleton. Fill in `[BRACKETED]` placeholders. Delete sections that don't apply to the document type (see Document Type Variants table below).

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>[CLIENT] — [PROJECT TITLE]</title>
<link rel="stylesheet" href="/Users/samotage/Documents/01_otagelabs/Foundational/Branding/document/otagelabs-document.css">
</head>
<body>

<!-- ==================== COVER PAGE ==================== -->
<div class="cover">
  <img src="file:///Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png" alt="otageLabs">
  <div class="cover-divider"></div>
  <div class="cover-title">[CLIENT NAME]</div>
  <div class="cover-subtitle">[PROJECT TITLE]</div>
  <div class="cover-type">[DOCUMENT TYPE — e.g. Phased Engagement Proposal]</div>
  <div class="cover-divider"></div>
  <div class="cover-meta">
    <strong>Prepared by:</strong> Sam Sabey, otageLabs<br>
    [DATE — e.g. 30 April 2026]<br>
    Confidential
  </div>
</div>

<!-- ==================== CONTENT PAGES ==================== -->
<div class="page-header">
  <img src="file:///Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png" alt="otageLabs">
  <div class="page-header-text">[CLIENT] &mdash; [SHORT PROJECT NAME]<br>[DATE]</div>
</div>

<div class="meta">
  <p><strong>Prepared for:</strong> [RECIPIENT NAME, TITLE &mdash; ORGANISATION]</p>
  <p><strong>Prepared by:</strong> Sam Sabey, otageLabs</p>
  <p><strong>Date:</strong> [DATE]</p>
  <p><strong>Engagement type:</strong> [e.g. Time and materials, phase-capped]</p>
  <p><strong>Estimated effort:</strong> [e.g. 16 hours (2 days)]</p>
</div>

<hr>

<!-- Section labels use spaced uppercase copper text -->
<div class="section-label">[SECTION NAME — e.g. Background]</div>

<p>[Body text. Use &rsquo; for apostrophes, &mdash; for em dashes, &ndash; for en dashes.]</p>

<!-- Bold-labelled bullet lists -->
<ul>
  <li><strong>[Label]</strong> &mdash; [description]</li>
  <li><strong>[Label]</strong> &mdash; [description]</li>
</ul>

<hr>

<div class="section-label">Scope of Work</div>

<!-- Phase headings -->
<h2>Phase 1 &mdash; [Phase Name]</h2>
<p class="phase-meta">[hours] &middot; [duration] &middot; [cost or engagement model]</p>

<h3>[Sub-section]</h3>
<ul>
  <li>[Item]</li>
</ul>

<!-- Flowchart: phase decision-flow diagram (use for multi-phase proposals) -->
<div class="flowchart">
  <div class="phase-card">
    <p class="phase-card-name">Phase 0 &mdash; [Phase Name]</p>
    <p class="phase-card-desc">[hours] &middot; [duration] &middot; [cost]</p>
  </div>
  <div class="gate">
    <div class="gate-line"></div>
    <div class="gate-label">Go / No-go</div>
    <div class="gate-line"></div>
  </div>
  <div class="phase-card">
    <p class="phase-card-name">Phase 1 &mdash; [Phase Name]</p>
    <p class="phase-card-desc">[hours] &middot; [duration] &middot; [cost]</p>
  </div>
  <!-- Add more phase-card + gate pairs as needed -->
  <!-- Use class="phase-card future" for phases not yet quoted -->
  <div class="gate">
    <div class="gate-line"></div>
    <div class="gate-label">Go / No-go</div>
    <div class="gate-line"></div>
  </div>
  <div class="phase-card future">
    <p class="phase-card-name">Phase N &mdash; [Future Phase]</p>
    <p class="phase-card-desc">Scoped and costed after Phase N-1</p>
  </div>
</div>

<hr>

<!-- Estimate / engagement terms table -->
<div class="section-label">Engagement Terms</div>

<table>
  <tr><th>Item</th><th class="r">Detail</th></tr>
  <tr><td><strong>Effort</strong></td><td class="r">[hours and engagement model]</td></tr>
  <tr><td><strong>Rate</strong></td><td class="r">$[rate] per hour</td></tr>
  <tr><td><strong>Total</strong></td><td class="r">$[total]</td></tr>
</table>

<!-- For multi-phase summary tables -->
<div class="section-label">Estimate</div>

<table>
  <tr><th>Phase</th><th>Scope</th><th>Effort</th><th>Duration</th><th class="r">Estimate</th></tr>
  <tr><td><strong>Phase 0</strong></td><td>[name]</td><td>[hours]</td><td>[weeks]</td><td class="r">$[cost]</td></tr>
  <tr><td><strong>Phase 1</strong></td><td>[name]</td><td>[hours]</td><td>[weeks]</td><td class="r">$[cost]</td></tr>
  <tr class="total"><td colspan="2"><strong>Total</strong></td><td><strong>[total hours]</strong></td><td><strong>[total weeks]</strong></td><td class="r"><strong>$[total]</strong></td></tr>
</table>

<p class="note">[Footnote text — conditions, exclusions, or context for the estimate.]</p>

<hr>

<div class="section-label">Assumptions</div>

<ul>
  <li>[Assumption 1]</li>
  <li>[Assumption 2]</li>
</ul>

<p class="sign-off">Issued by otageLabs, [DATE].</p>

</body>
</html>
```

## Component cookbook

### Cover page
```html
<div class="cover">
  <img src="file:///Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png" alt="otageLabs">
  <div class="cover-divider"></div>
  <div class="cover-title">Client Name</div>
  <div class="cover-subtitle">Project Title</div>
  <div class="cover-type">Document Type</div>
  <div class="cover-divider"></div>
  <div class="cover-meta">
    <strong>Prepared by:</strong> Sam Sabey, otageLabs<br>
    30 April 2026<br>
    Confidential
  </div>
</div>
```

### Page header (in-content, appears once after cover)
```html
<div class="page-header">
  <img src="file:///Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png" alt="otageLabs">
  <div class="page-header-text">Client &mdash; Project<br>30 April 2026</div>
</div>
```

### Section label (spaced uppercase copper)
```html
<div class="section-label">Section Name</div>
```

### Metadata block
```html
<div class="meta">
  <p><strong>Prepared for:</strong> Name, Title &mdash; Organisation</p>
  <p><strong>Prepared by:</strong> Sam Sabey, otageLabs</p>
  <p><strong>Date:</strong> 30 April 2026</p>
  <p><strong>Engagement type:</strong> Time and materials</p>
</div>
```

### Phase heading with metadata
```html
<h2>Phase 1 &mdash; Discovery</h2>
<p class="phase-meta">16 hours &middot; 2 days &middot; $2,560</p>
```

### Flowchart with phase cards and gates
```html
<div class="flowchart">
  <div class="phase-card">
    <p class="phase-card-name">Phase 0 &mdash; Discovery</p>
    <p class="phase-card-desc">30 hours &middot; 1&ndash;2 weeks &middot; $4,800</p>
  </div>
  <div class="gate">
    <div class="gate-line"></div>
    <div class="gate-label">Go / No-go</div>
    <div class="gate-line"></div>
  </div>
  <div class="phase-card">
    <p class="phase-card-name">Phase 1 &mdash; Implementation</p>
    <p class="phase-card-desc">50 hours &middot; 4 weeks &middot; $8,000</p>
  </div>
</div>
```

Use `class="phase-card future"` for phases not yet quoted (renders with dashed border).

### Tables
```html
<!-- Simple two-column -->
<table>
  <tr><th>Item</th><th class="r">Detail</th></tr>
  <tr><td><strong>Effort</strong></td><td class="r">16 hours</td></tr>
  <tr><td><strong>Rate</strong></td><td class="r">$160 per hour</td></tr>
  <tr><td><strong>Total</strong></td><td class="r">$2,560</td></tr>
</table>

<!-- Multi-column with total row -->
<table>
  <tr><th>Phase</th><th>Scope</th><th>Effort</th><th class="r">Estimate</th></tr>
  <tr><td><strong>Phase 0</strong></td><td>Discovery</td><td>30 hours</td><td class="r">$4,800</td></tr>
  <tr class="total"><td colspan="2"><strong>Total</strong></td><td><strong>30 hours</strong></td><td class="r"><strong>$4,800</strong></td></tr>
</table>
```

Use `class="r"` on `<th>` and `<td>` for right-aligned cells (costs, numbers). Use `class="total"` on `<tr>` for bold total rows with copper top border.

### Dividers
```html
<hr>              <!-- Copper 2px divider — use between major sections -->
<hr class="light"> <!-- Light 1px divider — use between sub-sections (e.g. between phases) -->
```

`<hr>` is a visible copper divider. It does NOT trigger page breaks. For explicit page breaks, use `<div class="page-break"></div>`.

### Utility classes
```html
<p class="note">Footnote or condition text.</p>
<p class="sign-off">Issued by otageLabs, 30 April 2026.</p>
<div class="no-break"><!-- Content that must not split across pages --></div>
<div class="page-break"></div> <!-- Force page break -->
```

### HTML entities reference
| Character | Entity | Use |
|-----------|--------|-----|
| Apostrophe / right single quote | `&rsquo;` | ICU&rsquo;s, don&rsquo;t |
| Em dash | `&mdash;` | Separators in text |
| En dash | `&ndash;` | Ranges: 1&ndash;2 weeks |
| Middle dot | `&middot;` | Phase meta separators: 30 hours &middot; 2 weeks |
| Times | `&times;` | Quantities: 3 &times; devices |

## Document type variants

Not every document uses every component. Use this table to determine which sections to include:

| Section | Proposal | Quotation | Technical Brief | Evaluation Report | Feasibility Analysis |
|---------|----------|-----------|-----------------|-------------------|---------------------|
| Cover | Yes | Yes | Yes | Yes | Yes |
| Page header | Yes | Yes | Yes | Yes | Yes |
| Meta block | Yes | Yes | Yes | Yes | Yes |
| Overview/Background | Yes | Yes | Yes (Context) | Yes (Context) | Yes (Context) |
| Approach | Yes | Optional | No | Yes (Methodology) | Yes (Assessment) |
| Flowchart | Yes (multi-phase) | Optional | No | No | No |
| Scope of Work | Yes | Yes (simplified) | No | No | No |
| Findings | No | No | Yes | Yes | Yes |
| Comparison table | No | No | Optional | Yes | Optional |
| Recommendation | Optional | No | Yes | Yes | Yes |
| Risks | Optional | Optional | Optional | Optional | Yes |
| Estimate table | Yes | Yes | No | No | No |
| Commercial Terms | Yes | Yes | No | No | No |
| Assumptions | Yes | Yes | Optional | Optional | Yes |
| Exclusions | Optional | Optional | No | No | Optional |
| Next Steps | Optional | Optional | Yes | Yes | Yes |
| Sign-off | Yes | Yes | Yes | Yes | Yes |

## Converting from markdown source

When the operator provides a markdown file as the content source:

1. Read the markdown to understand the content structure
2. Create a new HTML file using the skeleton above
3. Map markdown headings to the template structure:
   - `# Title` → `.cover-title`
   - `## Subtitle` → `.cover-subtitle` (first one) or `<h2>` (subsequent)
   - `### Sub-heading` → `<h3>`
   - Bold labels at start of content → `.section-label` divs
4. Preserve all content — the template adds visual structure, it does not edit prose
5. Use HTML entities for typographic characters (see entity reference above)
6. Fill in metadata from context (client name, date, engagement type)

## Verification gate

After rendering, verify the PDF against the canonical references:

**Brand parity bar (the gospel):** `/Users/samotage/Documents/01_otagelabs/Clients/ICU/projects/reverse_ingress/ICU_Solarcam_Reverse_Ingress_Quotation_Apr_2026.pdf`
**Template test render:** `/Users/samotage/Documents/01_otagelabs/Foundational/Branding/document/test-v2-render.pdf`
**Validated real-world output:** `/Users/samotage/Documents/01_otagelabs/Clients/ICU/projects/sip/sip-discovery-proposal-2026-04-30.pdf`

Check:
- Cover page: logo centred, copper dividers, title/subtitle/type hierarchy, metadata
- Page header: logo left, context text right, copper underline
- Section labels: spaced uppercase, copper
- Tables: copper header row with white text, alternating row backgrounds
- Footer: "otageLabs — Confidential" left, "Page N" right
- Dividers: copper `<hr>` between sections, light `<hr class="light">` between sub-sections
- Flowchart (if present): phase cards with copper left border, go/no-go gate pills

## Common pitfalls

**Margins:** Puppeteer's `mcp__puppeteer-pdf__file_to_pdf` defaults to 10mm margins. The document template requires 22/25/22/25mm. Always pass margin values explicitly — the CSS `@page` rule alone is not sufficient because Puppeteer does not expose `preferCSSPageSize`.

**Header template font-size:** Puppeteer renders header/footer templates at size 0 by default. The footer template includes `font-size:9pt` inline. If you modify the footer template, you must include explicit `font-size` or it will render invisible.

**`file://` prefix on images:** Logo paths in `<img src="...">` must use the `file:///` prefix. Without it, Puppeteer cannot resolve local file paths in the rendered page.

**`---` is a divider, not a page break:** Unlike MARP where `---` separates slides, in this template `<hr>` renders as a visible copper line. Use `<div class="page-break"></div>` for explicit page breaks.

**No inline styles:** All styling comes from `otagelabs-document.css`. Do not add `<style>` blocks to the HTML file. This is the exact anti-pattern the template exists to prevent — hand-cranked bespoke documents that diverge from the brand. If the CSS doesn't support a visual element you need, escalate to Maren to add it to the CSS.

**Long tables:** Tables that span page boundaries can split mid-row. Wrap critical table sections in `<div class="no-break">` to keep them together. For very long tables, consider splitting into multiple tables with repeated headers.

**Orphan headings:** A heading at the bottom of a page with content on the next page. Wrap the heading and its first paragraph in `<div class="no-break">` to prevent this.

**Content from markdown sources:** Markdown single-newlines are not line breaks. When converting metadata blocks or structured content from markdown, use `<p>` tags or `<br>` for each line. Blank lines in markdown become paragraph breaks — single newlines collapse to spaces.
