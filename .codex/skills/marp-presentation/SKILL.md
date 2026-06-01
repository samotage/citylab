---
name: marp-presentation
description: Generate slide decks from markdown using MARP. Use this skill when producing
  a presentation — slides for a meeting, briefing, workshop, pitch, board update,
  investor deck, or any deliverable where the audience and delivery context call for
  slide format rather than a document. Outputs HTML, PDF, or PPTX. Uses the otageLabs
  house theme by default.
allowed-tools:
- Read
- Write
- Edit
- Bash(marp *)
- Bash(ls *)
- Bash(mkdir -p *)
- Bash(open *)
version: 1.0.0
argument-hint: '[source.md] [--pdf|--pptx|--html]'
metadata:
  short-description: Generate slide decks from markdown using MARP.
---

# MARP Presentation

Convert markdown to slide decks using `marp-cli`. Output: HTML, PDF, or PPTX. Uses the otageLabs house theme automatically when invoked from a project with `.marprc.yml` or with the `--theme-set` flag.

## When to invoke this skill

Audience and delivery context drive the trigger, not content type:

- The operator explicitly requests a presentation ("make a deck", "slides for this", "presentation on X")
- The deliverable's audience is a group sitting through a presentation, not a reader of a document
- The delivery context is a meeting, workshop, briefing, pitch, board update, or investor presentation

Default output formats remain unchanged. Producing slides is an additive capability — it does not replace your normal document outputs.

## Default frontmatter (copy-paste starter)

Every MARP file starts with this block:

```markdown
---
marp: true
theme: otagelabs
paginate: true
---
```

- `marp: true` — required. MARP CLI ignores files without it.
- `theme: otagelabs` — references Maren's house theme. Resolved via `.marprc.yml` or `--theme-set`.
- `paginate: true` — slide numbers in bottom-right. Override per-deck if not wanted.

## Slide separators

Slides are separated by `---` on its own line. Everything after frontmatter is slides:

```markdown
---
marp: true
theme: otagelabs
---

# Slide one heading

Body content for slide one.

---

# Slide two heading

Body content for slide two.
```

## Key directives

Use these. Don't bother with the rest unless you have a specific need — link to https://marpit.marp.app/directives for the full set.

| Directive | Scope | Effect |
|---|---|---|
| `_class: lead` | next slide | Title slide layout |
| `_class: invert` | next slide | Dark-background slide |
| `_paginate: false` | next slide | Hide slide number on this slide |
| `_backgroundImage: url(...)` | next slide | Per-slide background image |

Underscore prefix (`_class:`) means slide-scoped (applies to next slide only). No underscore (`class:`) is global.

## Layout cookbook (otageLabs house theme)

The house theme provides these CSS classes. Use them via `<div class="...">` blocks inside slide markdown.

### Title slide

```markdown
---
_class: lead
_paginate: false
---

![w:200](/Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png)

# Presentation Title

Subtitle or tagline

Presenter Name · 2026-04-29
```

The logo line is the first content element on the slide — the theme positions it correctly when it leads the slide content.

### Section divider

```markdown
---
_class: lead
---

# S E C T I O N   T W O

Optional small subtitle
```

### Content slide (workhorse)

```markdown
---

# Heading

Body paragraph with the main point.

- Bullet point one
- Bullet point two
- Bullet point three
```

### Two-column layout

```markdown
---

# Heading spans the full width

<div class="columns">

**Left column**

Content for the left side.

**Right column**

Content for the right side.

</div>
```

Variants: `columns-33-67` (narrow left, wide right), `columns-67-33` (wide left, narrow right).

### Stats slide

```markdown
---

# Stats heading

<div class="stat-hero">42%</div>
<div class="stat-label">conversion uplift</div>
```

`stat-hero` is the largest stat size; `stat-big` is medium. Pair with `stat-label` for caption text.

### Status indicators (in tables, prose, or headings)

```markdown
- <span class="status-green">On track</span> — milestone delivered
- <span class="status-amber">At risk</span> — schedule slippage
- <span class="status-red">Blocked</span> — needs intervention
```

### Caption / label text

```markdown
<div class="label">F I N D I N G S</div>
<div class="caption">Source: 2026-04 customer interviews, n=14</div>
```

## CLI commands (the shortlist)

**Always pass `--config-file ~/.marprc.yml`.** This loads the global otageLabs config that registers the house theme and enables local-file access (logos, images). It works from any current directory — claude_headspace, kenwood, /tmp, anywhere. Without this flag, `theme: otagelabs` won't resolve and absolute logo paths will be blocked.

```bash
marp deck.md --config-file ~/.marprc.yml                          # → HTML (default)
marp deck.md --config-file ~/.marprc.yml --pdf                    # → PDF
marp deck.md --config-file ~/.marprc.yml --pptx                   # → PowerPoint
marp deck.md --config-file ~/.marprc.yml -o output-name.pdf       # → specify output filename
marp deck.md --config-file ~/.marprc.yml -s .                     # → local server with live preview
marp deck.md --config-file ~/.marprc.yml -w                       # → watch mode (auto-rebuild on save)
```

When to use which:
- **HTML** — viewing in a browser, sharing a link, embedding in web
- **PDF** — client delivery, email attachments, archival
- **PPTX** — recipient needs to edit slides in PowerPoint or Keynote
- **Live preview (`-s`)** — iterative drafting, see changes immediately
- **Watch mode (`-w`)** — longer design sessions, rebuild on save

## otageLabs logo paths

The logo files live at `/Users/samotage/Documents/01_otagelabs/Foundational/Logo/`. The CSS theme does NOT auto-inject logos — you place them explicitly in markdown using MARP's image syntax with width control: `![w:200](absolute/path.png)`.

Use the variant that matches the slide background:

| Variant | Path | Use on |
|---|---|---|
| Light-bg (preferred for default white slides) | `/Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-light-bg_v1.0.png` | Title slide, content slides, anything with `_class: lead` or default white background |
| Standard (for dark slides) | `/Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo_v1.0.png` | Slides with `_class: invert` or `_class: dark` |
| Transparent (for backgrounds with imagery) | `/Users/samotage/Documents/01_otagelabs/Foundational/Logo/otagelabs-logo-transparent_v1.0.png` | Slides with custom background images |

**Rules:**
- Use absolute paths, not relative — the theme is registered globally, your deck may not be in the same directory tree
- Width: `w:200` for title slides, `w:120` for header positions on content slides
- Do NOT add a logo to every slide — the title slide and the closer slide are sufficient for branding
- For client-branded work, swap to the client's logo and document the departure from house theme

## Theme registration

The house theme lives at `/Users/samotage/Documents/01_otagelabs/Foundational/Branding/marp/otagelabs.css`.

**Global config at `~/.marprc.yml`** registers the theme and enables local-file access for any deck rendered anywhere on the system. The file content:

```yaml
themeSet:
  - /Users/samotage/Documents/01_otagelabs/Foundational/Branding/marp/otagelabs.css
allowLocalFiles: true
html: true
```

Always pass `--config-file ~/.marprc.yml` to marp-cli (see CLI commands above). This is the only setup needed — no per-project `.marprc.yml`, no `--theme-set` flag, no `--allow-local-files` flag. One config, used from anywhere.

If `~/.marprc.yml` is missing or corrupt, recreate it from the block above. The CSS path inside it is the canonical source of truth for the theme.

## Theme is owned by Maren — do not modify

The CSS is Maren's. Do not edit `otagelabs.css` directly. If the theme doesn't support what a deck needs (new layout, different colour, new component), escalate to Maren. Do not hack around it with inline `<style>` blocks — that breaks brand consistency across the portfolio.

## Escalation to Maren for high-stakes decks

When a presentation is **client-facing, investor-facing, board-level, or otherwise high-stakes**, hand the source `.md` off to Maren for design-grade production. The house theme gets you 80% of the way; Maren brings the last 20% — and for high-stakes work, the last 20% is what matters.

Self-serve path is for:
- Internal sprint reviews, status briefings, workshop summaries
- Architecture walkthroughs for the team
- Working presentations where content matters more than polish

Maren-finalised path is for:
- Pitch decks, investor presentations, board updates
- Client-facing material, sales collateral
- Anything where visual craft is part of the message

## Output and save conventions

- Save MARP source files as `.md` (not `.marp.md` — MARP detects from frontmatter)
- Save rendered output to a project-relative path so it's viewable in the Headspace preview viewer
- Never write output files to `otl_support`, `.claude`, or any directory outside the project root
- Report completed presentations with the **full absolute path** to both the source `.md` and the rendered output (`.html`, `.pdf`, or `.pptx`)

## Verification before delivery

1. Render the deck (`marp deck.md --pdf`)
2. Open the output (`open deck.pdf`) and read every slide
3. Check: does each slide read in a single glance? Is there overflow? Are tables breaking? Are images loading?
4. If anything looks wrong, fix the source and re-render. Do not deliver an unviewed render.

## Common pitfalls

- **Forgetting `marp: true`** — marp-cli silently does nothing on files without it
- **`---` collisions** — every `---` outside frontmatter is a slide break. Don't use `---` as a horizontal rule inside a slide.
- **Inline CSS to override the theme** — escalate to Maren instead. The brand is the brand.
- **Absolute image paths** — use project-relative paths so the deck is portable
- **Skipping the render-and-open verification step** — text that fits in markdown often overflows when rendered to a fixed slide size

## Reference

- MARP official: https://marp.app/
- Marpit directives: https://marpit.marp.app/directives
- otageLabs Brand Guidelines: `/Users/samotage/Documents/01_otagelabs/Foundational/otageLabs-Brand-Guidelines.md`
- House theme CSS: `/Users/samotage/Documents/01_otagelabs/Foundational/Branding/marp/otagelabs.css`
- Project config: `claude_headspace/.marprc.yml`
