---
name: generate-pdf
description: Generate a PDF from an HTML file using WeasyPrint, or capture a live
  web page using Puppeteer. Use this skill when asked to create, export, or generate
  a PDF.
allowed-tools:
- mcp__puppeteer-pdf__url_to_pdf
- Read
- Write
- Bash(weasyprint *)
- Bash(ls *)
- Bash(mkdir -p *)
version: 2.0.0
argument-hint: '[file|url] [source] [output_filename]'
metadata:
  short-description: Generate a PDF from an HTML file using WeasyPrint, or capture
    a live web page using Puppeteer.
---

# Generate PDF

Two engines, one routing rule:

| Source | Engine | Tool |
|--------|--------|------|
| HTML file on disk | **WeasyPrint** (default) | `weasyprint` CLI via Bash |
| Live web page / URL | **Puppeteer** | `mcp__puppeteer-pdf__url_to_pdf` |

**WeasyPrint is the default.** Use it for all document generation — reports, briefs, proposals, infographics, any HTML-to-PDF conversion.  It correctly implements CSS Paged Media Level 3: `break-inside: avoid`, `break-after`, `break-before`, `@page` margin boxes, and widow/orphan control all work as specified.

**Puppeteer is for URL captures only** — live web pages with JavaScript-rendered content.  Do NOT use Puppeteer for HTML file → PDF conversion.

## WeasyPrint (HTML File → PDF)

### Basic command

```bash
weasyprint /absolute/path/to/input.html /absolute/path/to/output.pdf
```

### With options

```bash
weasyprint input.html output.pdf \
  --stylesheet extra-styles.css \
  --base-url /absolute/path/to/asset-directory/ \
  --presentational-hints
```

| Flag | Purpose |
|------|---------|
| `--stylesheet` | Additional CSS file applied on top of the HTML's embedded styles |
| `--base-url` | Base URL for resolving relative asset paths (images, fonts) |
| `--presentational-hints` | Honour HTML presentational attributes (`width`, `bgcolor`, etc.) |

### Page setup via CSS (not tool parameters)

WeasyPrint reads page configuration from CSS `@page` rules in the HTML `<style>` block.  Margins, page size, orientation, headers, and footers are all CSS — not CLI flags.

```css
@page {
  size: A4 portrait;
  margin: 25mm 20mm 30mm 20mm;

  @bottom-center {
    content: "Company Name — Confidential";
    font-family: Arial, sans-serif;
    font-size: 8pt;
    color: #8A8480;
  }

  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-family: Arial, sans-serif;
    font-size: 8pt;
    color: #8A8480;
  }
}

@page :first {
  @bottom-center { content: none; }
  @bottom-right { content: none; }
}
```

### Page break CSS (works correctly in WeasyPrint)

```css
h2, h3, h4 { break-after: avoid; }
.no-break { break-inside: avoid; }
table { break-inside: avoid; }
```

These rules work as written.  No wrapper-sizing heuristics needed — WeasyPrint's fragmentainer backtracks correctly when content doesn't fit.

### Output path

- Always use absolute paths for both input and output
- Parent directories must exist — create with `mkdir -p` if needed
- Output lands exactly where specified

## Puppeteer (URL → PDF)

For capturing live web pages only.

### `mcp__puppeteer-pdf__url_to_pdf`

**Required parameters:**
- `url` — the URL to navigate to
- `output_path` — filename (saves to `~/Downloads/`) or absolute path

**Optional:**
- `wait_for_selector` — CSS selector to wait for before generating
- `wait_for_timeout` — milliseconds to wait after page load
- `format` — page size (default `A4`)
- `landscape` — `"auto"` (default), `"true"`, or `"false"`
- `print_background` — include backgrounds (default `true`)
- `margin_top`, `margin_bottom`, `margin_left`, `margin_right` — margins (default `10mm`)
- `display_header_footer` — show header/footer (default `false`)
- `header_template`, `footer_template` — HTML templates for headers/footers

### Example

```
mcp__puppeteer-pdf__url_to_pdf({
  url: "https://example.com/dashboard",
  output_path: "dashboard.pdf",
  wait_for_timeout: 3000
})
```

## Known WeasyPrint limitations

- **No JavaScript execution** — JS-rendered content won't appear.  Use Puppeteer for those
- **No flexbox or CSS grid** — use traditional layout (floats, tables, inline-block).  This is fine for documents
- **`box-shadow` unsupported** — cosmetic only, renders without shadow
- **`print-color-adjust: exact` unknown** — not needed; WeasyPrint prints backgrounds by default

## Tips

- **Margins go in CSS `@page`, not in CLI flags.**  WeasyPrint's CLI has no margin flags — all page setup is CSS
- **Headers and footers go in `@page` margin boxes** (`@top-center`, `@bottom-right`, etc.) — not in tool parameters
- **Use `--base-url`** when your HTML references relative image paths — set it to the directory containing the assets
- **Use `--presentational-hints`** when converting HTML that uses inline `width`, `height`, `bgcolor` attributes
- **For landscape:** use `@page { size: A4 landscape; }` in CSS
- **For different page sizes:** use `@page { size: A3; }`, `@page { size: Letter; }`, etc.
