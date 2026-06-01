---
name: docx-to-markdown
description: Convert Microsoft Word (.docx) files to clean Markdown using pandoc. Use when importing Word documents into a project, extracting content for version control, converting client documents to editable markdown, or preparing docx content for AI processing. Also handles .doc (legacy) via LibreOffice conversion.
allowed-tools:
  - Read
  - Bash(pandoc *)
  - Bash(ls *)
  - Bash(mkdir -p *)
  - Bash(file *)
version: 1.0.0
argument-hint: "[path/to/document.docx] [--images] [--output path/to/output.md]"
---

# Docx to Markdown

Convert Microsoft Word documents (.docx) to clean Markdown using `pandoc`.  Produces well-structured GitHub-Flavoured Markdown with optional image extraction.

## When to invoke this skill

- Importing a Word document into a project or repository
- Extracting content from a .docx for editing, review, or AI processing
- Converting client-provided documents to markdown for version control
- Preparing document content for inclusion in briefs, specs, or knowledge bases

**Not this skill:**
- Creating or editing Word documents → use `/generate-docx`
- PDF generation → use `/generate-pdf` or `/document-template`
- Spreadsheets (.xlsx) or presentations (.pptx)

## Dependencies

- **pandoc** (required) — `brew install pandoc`
- **LibreOffice** (optional, for legacy .doc files) — `brew install --cask libreoffice`

## Quick start

```bash
# Basic conversion — outputs document.md alongside the source
pandoc document.docx -t gfm -o document.md

# With image extraction to a media/ folder
pandoc document.docx -t gfm --extract-media=./document_media -o document.md

# With tracked changes visible (all marks shown)
pandoc document.docx -t gfm --track-changes=all -o document.md

# Accept all tracked changes (clean output)
pandoc document.docx -t gfm --track-changes=accept -o document.md
```

## Workflow

### 1. Check the source file

```bash
file document.docx
```

If it's a `.doc` (legacy), convert to `.docx` first:
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to docx document.doc
```

### 2. Choose conversion mode

**Text only (no images):**
```bash
pandoc input.docx -t gfm -o output.md
```

**With images extracted to folder:**
```bash
pandoc input.docx -t gfm --extract-media=./output_media -o output.md
```
Images are saved to the media folder and referenced with relative paths in the markdown.

**With tracked changes:**
```bash
# Show all changes (insertions, deletions, comments visible)
pandoc input.docx -t gfm --track-changes=all -o output.md

# Accept all changes (clean document)
pandoc input.docx -t gfm --track-changes=accept -o output.md

# Reject all changes (original text only)
pandoc input.docx -t gfm --track-changes=reject -o output.md
```

### 3. Post-process (if needed)

Pandoc produces clean GFM by default.  Occasionally, Word documents contain artifacts that benefit from cleanup:

**Common cleanup patterns:**
- Empty heading anchors: `{#section}` suffixes on headings — strip with `sed 's/ {#[^}]*}$//'`
- Excessive blank lines — collapse with `sed '/^$/N;/^\n$/d'`
- Non-breaking spaces — replace with `sed 's/\xC2\xA0/ /g'`
- Smart quotes to straight quotes (if needed for code contexts) — `sed "s/[\x{2018}\x{2019}]/'/g; s/[\x{201C}\x{201D}]/\"/g"`

### 4. Verify output

Read the generated markdown and confirm:
- Heading hierarchy is intact (H1 → H2 → H3, no skipped levels)
- Tables converted to GFM pipe tables
- Lists preserved (ordered and unordered)
- Images referenced correctly (if extracted)
- No mangled Unicode or encoding issues

## Batch conversion

```bash
for f in *.docx; do
  [ -e "$f" ] || continue
  name="${f%.docx}"
  pandoc "$f" -t gfm --extract-media="./${name}_media" -o "${name}.md"
  echo "Converted: $f → ${name}.md"
done
```

## Output formats

Pandoc supports multiple markdown flavours.  Default to `gfm` (GitHub-Flavoured Markdown) unless the operator specifies otherwise:

| Flag | Format | Use when |
|------|--------|----------|
| `-t gfm` | GitHub-Flavoured Markdown | Default — tables, fenced code, task lists |
| `-t markdown` | Pandoc Markdown | Need footnotes, definition lists, or metadata |
| `-t commonmark` | CommonMark | Strict compatibility needed |

## Pandoc options reference

| Option | Purpose |
|--------|---------|
| `-t gfm` | Output format (GitHub-Flavoured Markdown) |
| `-o output.md` | Output file path |
| `--extract-media=./dir` | Extract images to directory |
| `--track-changes=accept` | Accept tracked changes (clean output) |
| `--track-changes=all` | Show all tracked changes |
| `--track-changes=reject` | Reject tracked changes |
| `--wrap=none` | No line wrapping (one paragraph = one line) |
| `--columns=80` | Wrap at 80 columns |
| `--standalone` | Include YAML metadata block |
| `--toc` | Generate table of contents |
| `--reference-links` | Use reference-style links instead of inline |

## Common pitfalls

**Tables with merged cells.**  GFM pipe tables don't support cell spans.  Pandoc will approximate — check the output and restructure if needed.

**Complex layouts.**  Multi-column layouts, text boxes, and floating elements don't have markdown equivalents.  Content is extracted but layout is lost.  This is expected.

**Embedded OLE objects.**  Charts, embedded Excel sheets, and other OLE objects are not extracted.  Note their absence in the output.

**Image paths.**  `--extract-media` creates a folder with images named `image1.png`, `image2.png`, etc.  The markdown references these with relative paths.  If you move the markdown file, update the image paths or move the media folder with it.

**Large documents.**  Pandoc handles large documents well, but very complex files (hundreds of tracked changes, deeply nested tables) may produce verbose output.  Post-process as needed.

**Encoding.**  Pandoc assumes UTF-8 input.  If the document contains legacy encoding, convert first or use `--from docx`.
