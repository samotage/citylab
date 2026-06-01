---
name: generate-docx
description: Generate an editable Word (.docx) document using the mcp-doc MCP tools. Use when the operator asks for an editable document, a Word file, a docx, or when the deliverable needs to be handed off to a client or stakeholder for further editing. NOT for PDF-grade branded proposals — use /document-template for those.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(ls *)
  - Bash(mkdir -p *)
  - mcp__mcp-doc__create_document
  - mcp__mcp-doc__open_document
  - mcp__mcp-doc__get_document_info
  - mcp__mcp-doc__add_heading
  - mcp__mcp-doc__add_paragraph
  - mcp__mcp-doc__add_page_break
  - mcp__mcp-doc__add_table
  - mcp__mcp-doc__add_table_row
  - mcp__mcp-doc__edit_table_cell
  - mcp__mcp-doc__merge_table_cells
  - mcp__mcp-doc__delete_paragraph
  - mcp__mcp-doc__delete_table_row
  - mcp__mcp-doc__delete_text
  - mcp__mcp-doc__find_and_replace
  - mcp__mcp-doc__replace_section
  - mcp__mcp-doc__edit_section_by_keyword
  - mcp__mcp-doc__search_text
  - mcp__mcp-doc__set_page_margins
  - mcp__mcp-doc__save_document
  - mcp__mcp-doc__save_as_document
  - mcp__mcp-doc__create_document_copy
  - mcp__mcp-doc__split_table
version: 1.0.0
argument-hint: "[source content, .md file, or brief description] [output path]"
---

# Generate Docx

Produce an editable Word document (.docx) using the `mcp__mcp-doc__*` MCP tools.  The output is a structured, styled document that the recipient can open in Microsoft Word and edit directly.

## When to invoke this skill

- The operator asks for an editable document, Word file, or docx
- The deliverable is being handed to a client or stakeholder who needs to make their own edits
- Help documents, guides, handover docs, SOPs, reports where editability matters more than pixel-perfect branding

**Not this skill:**
- Pixel-perfect branded proposals/quotations where the recipient should NOT edit → use `/document-template` (PDF pipeline)
- Slide decks → use `/marp-presentation`
- Internal notes, READMEs → plain markdown

## Pipeline

```
Content source (markdown, conversation, structured brief)
  → mcp__mcp-doc__create_document (new file)
  → set_page_margins (professional layout)
  → build structure (headings, paragraphs, tables, page breaks)
  → save_document
  → verify via get_document_info
```

## Workflow

### 1. Establish design context

**If the document carries client branding** — read any available brand guidelines, existing client documents, or style references before building.  Match their heading fonts, colours, and logo placement.  The operator or Maren will specify these.

**If the document carries otageLabs branding** — read the brand guidelines at:
```
/Users/samotage/Documents/01_otagelabs/Foundational/Branding/
```

**If no brand context is specified** — use clean professional defaults: black body text, standard heading hierarchy, no colour accents.  The recipient can restyle in Word.

### 2. Plan the document structure

Before calling any mcp-doc tools, plan the full document structure:
- Title and subtitle
- Section hierarchy (map to heading levels 1–3)
- Tables needed (rows, columns, header rows)
- Page breaks between major sections
- Any images or logos to include

### 3. Create the document

```
mcp__mcp-doc__create_document  →  file_path: "/path/to/output.docx"
```

Choose a sensible output path.  If the operator specified one, use it.  Otherwise, place the file in the relevant client or project directory.

### 4. Set margins

```
mcp__mcp-doc__set_page_margins  →  top: 2.54, bottom: 2.54, left: 2.54, right: 2.54
```

Standard 1-inch (2.54cm) margins.  Adjust if the design context calls for different spacing.

### 5. Build the document

Use the tools in sequence to assemble the document top-to-bottom:

**Headings:**
```
mcp__mcp-doc__add_heading  →  text: "Section Title", level: 1
```
- Level 1: document title and major sections
- Level 2: subsections
- Level 3: sub-subsections
- Do not skip levels (no jumping from 1 to 3)

**Body text:**
```
mcp__mcp-doc__add_paragraph  →  text: "...", font_name: "Calibri", font_size: 11
```
- One call per paragraph — do not concatenate multiple paragraphs into one call
- Use `bold`, `italic`, `alignment` parameters for inline formatting
- Use `color` (hex format `#FF0000`) for coloured text (headings, labels)
- Use `font_name` and `font_size` to match brand typography

**Tables:**
```
mcp__mcp-doc__add_table  →  rows: N, cols: M, data: [["Header1", "Header2"], ["val1", "val2"]]
```
- First row is typically the header row
- Use `edit_table_cell` to update individual cells after creation
- Use `merge_table_cells` for spanning headers or grouped rows
- Use `add_table_row` to append rows after initial creation

**Page breaks:**
```
mcp__mcp-doc__add_page_break
```
- Between major sections (cover → content, between chapters)
- Before appendices or reference sections

### 6. Save

```
mcp__mcp-doc__save_document
```

### 7. Verify

```
mcp__mcp-doc__get_document_info
```
Confirm paragraph count, table count, and section count match your plan.

## Editing existing documents

To modify an existing docx:

1. `open_document` → load the file
2. `get_document_info` → understand current structure
3. `search_text` → find the content to modify
4. Use `replace_section`, `edit_section_by_keyword`, `find_and_replace`, `edit_table_cell`, `delete_paragraph`, or `delete_table_row` as needed
5. `save_document` or `save_as_document` (new filename to preserve the original)

**Always `save_as_document` with a new name when editing a client's original** — never overwrite their source file.

## Converting from markdown

When the source content is a markdown file:

1. Read the markdown to understand structure
2. Map markdown elements to docx tools:
   - `# Heading` → `add_heading` level 1
   - `## Heading` → `add_heading` level 2
   - `### Heading` → `add_heading` level 3
   - Body paragraphs → `add_paragraph`
   - `**bold**` → `add_paragraph` with `bold: true` (or split into multiple runs if mixed)
   - Bullet lists → `add_paragraph` with `"• Item text"` (Word doesn't have a native list via this API)
   - Tables → `add_table` with `data` array
   - `---` → `add_page_break`
3. Preserve all content — the conversion adds document structure, it does not edit prose
4. Use proper typographic characters: smart quotes, em dashes (—), en dashes (–)

## Bullet and numbered lists

The mcp-doc API does not have a dedicated list tool.  Simulate lists:

**Bullet lists:**
```
add_paragraph  →  text: "•  Item text"
```

**Numbered lists:**
```
add_paragraph  →  text: "1.  First item"
add_paragraph  →  text: "2.  Second item"
```

Indent sub-items with leading spaces in the text.

## Tool reference

| Tool | Purpose |
|------|---------|
| `create_document` | Create new empty docx |
| `open_document` | Open existing docx for reading/editing |
| `get_document_info` | Paragraph count, table count, styles — use for verification |
| `add_heading` | Add heading (levels 1–9) |
| `add_paragraph` | Add body text with optional formatting |
| `add_table` | Create table with data |
| `add_table_row` | Append row to existing table |
| `edit_table_cell` | Update single cell content |
| `merge_table_cells` | Merge cell range (spanning headers, grouped rows) |
| `delete_paragraph` | Remove paragraph by index |
| `delete_table_row` | Remove table row by index |
| `delete_text` | Remove text range within a paragraph |
| `find_and_replace` | Global find-and-replace |
| `replace_section` | Replace content under a heading |
| `edit_section_by_keyword` | Replace content around a keyword match |
| `search_text` | Find text occurrences in document |
| `set_page_margins` | Set page margins (cm) |
| `add_page_break` | Insert page break |
| `save_document` | Save to original path |
| `save_as_document` | Save to new path (preserves original) |
| `create_document_copy` | Copy current document with suffix |
| `split_table` | Split table at specified row |

## Common pitfalls

**One paragraph per call.**  `add_paragraph` creates one paragraph.  If you pass a multi-line string, it becomes one paragraph with line breaks — not separate paragraphs.  Call once per paragraph.

**Table data is row-major.**  The `data` parameter is `[["row1col1", "row1col2"], ["row2col1", "row2col2"]]`.  First inner array is the first row (typically headers).

**No native list styles.**  Use bullet characters (`•`) or numbers in the text.  The recipient can convert to Word's native list styles if they want.

**Fonts must exist on the recipient's machine.**  Stick to widely available fonts: Calibri, Arial, Times New Roman, Segoe UI.  If using brand-specific fonts, note this in the handover.

**Images are not supported via this API.**  The mcp-doc tools do not include an `add_picture` tool.  If images are needed, add a placeholder paragraph noting where the image should go, and the recipient inserts it in Word.  Alternatively, produce the document with placeholders and note the image locations in the handover.

**Overwriting originals.**  When editing a client's file, always `save_as_document` with a new name.  Never `save_document` on a client original unless explicitly instructed.

**Paragraph indexing.**  `delete_paragraph`, `delete_text` use 0-based paragraph indices.  After deleting a paragraph, all subsequent indices shift down by 1.  Delete from bottom-up to avoid index drift.
