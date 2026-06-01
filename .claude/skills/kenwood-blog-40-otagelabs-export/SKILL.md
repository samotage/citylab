---
name: kenwood-blog-40-otagelabs-export
description: "Pipeline step 4/6. Automatic — runs after approval. Export an approved content piece to the otageLabs website blog. Transforms frontmatter, copies storyboard images, starts dev server. No operator gates."
license: MIT
metadata:
  author: otagelabs
  version: "2.0"
---

Export a Kenwood content piece to the otageLabs website blog.  Handles frontmatter translation, storyboard image copying, and dev server startup.

**This skill runs automatically as part of the publishing pipeline after content approval.**  It does not wait for operator input at any step.  If invoked manually, it behaves identically.

**Trigger:** Automatic after approval transition, or user says "export content piece to blog", "publish to otagelabs", "export to blog", or references exporting a content piece by ID.

---

## Paths

| Location | Path |
|----------|------|
| Kenwood project root | `/Users/samotage/dev/otagelabs/automations/kenwood` |
| Website project root | `/Users/samotage/dev/otagelabs/v0-otage-labs-website-design` |
| Website blog content | `{website}/content/blog/` |
| Website blog images | `{website}/public/blog/` |
| Kenwood storyboard images | `{kenwood}/content/storyboards/{kenwood_slug}/` |
| Website dev server script | `{website}/scripts/restart-server.sh` |

---

## Input

A content piece ID (integer).

**Resolution order:**
1. If the user provides an ID explicitly (e.g., "export content piece 42"), use it
2. If the user provides a website file path (e.g., `content/blog/my-post.md`), derive the slug from the filename and look up via `cli-kenwood content list --search <slug>`
3. If the user provides a title or partial reference, search via `cli-kenwood content list --search <query>` and match on title or slug.  Ask for disambiguation if multiple matches are found.
4. If the conversation has been working on a specific content piece and the ID is unambiguous, use it
5. If the ID cannot be determined from context, ask the user: "Which content piece should I export?  Provide the ID, or I can list recent content pieces for you."
6. If the user asks to see options, run `cli-kenwood content list --status approved --limit 10` and present the results for selection

**Do not guess.**  If there is any ambiguity about which content piece to export, ask.

---

## Step 1: Gather data from Kenwood

Run these commands from the Kenwood project root.  All three are independent; run them in parallel.

```bash
cli-kenwood content get <ID>
```
Captures: `id`, `title`, `slug`, `status`, `tags`, `summary`, `meta_description`, `created_at`.

**MC:** After gathering data, surface the content piece: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID> --navigate`

```bash
cli-kenwood content body <ID>
```
Captures: raw markdown (frontmatter + body).  Extract only the body (everything after the second `---` line).

```bash
cli-kenwood storyboards list --content-id <ID>
```
Captures: storyboard metadata and frames.  If no storyboard exists, this returns an error — that is fine.  Proceed without images.

---

## Step 1b: Status gate

After gathering data, check the `status` field from `cli-kenwood content get`.

| Status | Action |
|---|---|
| `approved`, `exported`, `aeo_optimised`, `scheduled`, `published` | Proceed with export (re-export is idempotent). |
| `draft` | **Reject.**  Tell the user: "Content piece #{id} is in {status} — it needs to be approved before export.  Run `/kenwood-blog-30-approve-content` to workshop the editorial metadata and approve it."  Stop. |
| `cancelled`, `archived` | **Reject.**  Tell the user: "Content piece #{id} is {status} and cannot be exported."  Stop. |

**This gate is non-negotiable.**  The `approved` status is a trust boundary — it guarantees that summary, meta_description, and tags are populated.  Exporting unapproved content bypasses that guarantee and produces blog posts with missing metadata.

---

## Step 2: Derive slugs

The Kenwood slug format is `{YYYY-MM-DD}-{title-slug}-{id}`.

From the `slug` field in the `cli-kenwood content get` JSON output, derive:

| Value | Derivation | Example |
|-------|-----------|---------|
| `kenwood_slug` | The full slug as-is | `2026-03-14-robot-meetings-need-minutes-too-42` |
| `blog_file_slug` | Strip the trailing `-{id}` (remove everything from the last hyphen followed by only digits at the end) | `2026-03-14-robot-meetings-need-minutes-too` |
| `url_slug` | Strip the `YYYY-MM-DD-` date prefix from `blog_file_slug` | `robot-meetings-need-minutes-too` |
| `post_date` | Extract the `YYYY-MM-DD` prefix from `blog_file_slug` | `2026-03-14` |

**Parsing rule for stripping the ID suffix:**  The ID is always the last segment after the final hyphen, and it consists of only digits.  Use a regex like `-\d+$` to strip it.  Be careful: title slugs can contain numbers (e.g., `top-10-tips-42` — strip only `-42`, not `-10`).

---

## Step 3: Determine image strategy

Based on the storyboard data from Step 1:

| Condition | Strategy |
|-----------|----------|
| No storyboard exists | **Text-only post.** No image fields in frontmatter. Skip Step 5. |
| Storyboard has exactly 1 completed frame | **Featured image only.** Use `featured_image` in frontmatter. |
| Storyboard has >1 completed frames | **Featured image + image sequence.** Use both `featured_image` (frame 01, serves as listing thumbnail and OG image) and `image_sequence` (drives in-post slideshow) in frontmatter. |

Only count frames where `generation_status` is `complete`.

---

## Step 4: Build and write the blog post

### Frontmatter

Build this YAML frontmatter block.  Field order matters for readability.

```yaml
---
title: "{title from content get}"
slug: {url_slug}
date: "{post_date}"
author: Sam Sabey
tags: [{tags array from content get}]
summary: "{summary from content get}"
meta_description: "{meta_description from content get}"
published: true
kenwood_slug: {kenwood_slug}
{image fields — see below}
---
```

**Image fields:**

For a single featured image (1 completed frame):
```yaml
featured_image: "/blog/{blog_file_slug}/01.webp"
```

For a storyboard with multiple frames (>1 completed frames) — include **both**:
```yaml
featured_image: "/blog/{blog_file_slug}/01.webp"
image_sequence:
  path: "/blog/{blog_file_slug}/"
  count: {number of completed frames}
  format: "webp"
  padDigits: 2
  transition: "crossfade"
```

`featured_image` serves as the listing page thumbnail and OG image.  `image_sequence` drives the in-post slideshow.  Both are needed when a storyboard has multiple frames.

For text-only: omit image fields entirely.

### Body

Use the body extracted from `cli-kenwood content body` (everything after the closing `---` of the Kenwood frontmatter).  Copy verbatim — no transformation.

### Write the file

Combine frontmatter + body and write to:
```
{website}/content/blog/{blog_file_slug}.md
```

**If the file already exists, overwrite it without prompting.**  The export is idempotent.

---

## Step 5: Copy storyboard images

**Skip this step if the post is text-only (no storyboard).**

### Source

WebP images from:
```
{kenwood}/content/storyboards/{kenwood_slug}/*.webp
```

Only copy `.webp` files.  Do not copy `.png` files.

### Destination

```
{website}/public/blog/{blog_file_slug}/
```

Create the directory if it does not exist.

### Copy operation

Copy each `.webp` file, preserving the sequential filenames (`01.webp`, `02.webp`, etc.).  The source and destination filenames are identical — no renaming needed.

Verify after copying:
- Count of `.webp` files in the destination matches the storyboard's completed frame count
- If counts do not match, report the discrepancy but do not fail

---

## Step 6: Start the dev server

Run the website dev server so the post is reviewable:

```bash
cd {website} && bash scripts/restart-server.sh
```

If the server is already running, this script handles restart.  Do not attempt to check whether it is running first — the script is idempotent.

---

## Step 7: Status transition

**Goal:** Move the content piece to `exported` in Kenwood.

This step runs after the export is confirmed successful.  The exported files are the primary deliverable — a failed transition does not undo them.

```bash
cli-kenwood content transition <ID> --action export
```

If the transition succeeds:

**MC:** Surface the updated entity: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID>`

**MC:** Notify the operator: `cli-kenwood mc notify --message "Content piece '{title}' exported to website repo"`

If the transition fails, report the error but **halt the pipeline**.  The operator is notified via flash banner with the failure reason.

```
Pipeline halted: Status transition to 'exported' failed: {error message}
The export files are written, but the status could not be updated.
```

---

## Step 8: Report

Print a summary:

```
Export complete.

  Content piece:  #{id} — {title}
  Kenwood slug:   {kenwood_slug}
  Blog file:      content/blog/{blog_file_slug}.md
  Images:         {count} webp files → public/blog/{blog_file_slug}/
                  (or "None — text-only post")
  Dev server:     Started

  Preview:        http://localhost:3000/blog/{url_slug}

Proceeding to SEO optimisation...
```

---

## Pipeline failure handling (FR8)

If any step in this skill fails:
- **Halt the pipeline immediately.**  Do not proceed to the next step.
- **Notify the operator** via flash banner: `cli-kenwood mc notify --message "Export failed: {reason}.  Content piece remains at approved."`
- **Do not retry automatically.**  The operator decides whether to retry or investigate.

---

## Error handling

| Error | Action |
|-------|--------|
| Content piece not found | Halt pipeline.  Notify operator. |
| Content piece has no markdown file | Halt pipeline.  Notify operator: "Content piece {id} has no markdown file." |
| Storyboard has no completed frames | Treat as text-only post (no images).  Continue. |
| Storyboard image directory missing | Report discrepancy but continue without images. |
| Website project directory missing | Halt pipeline.  Notify operator. |
| Dev server script fails | Report but continue — the files are already written. |

---

## DO NOT

- Ask for overwrite confirmation — the export is idempotent
- Wait for operator input between steps
- Reference manual invocation of subsequent pipeline skills — the pipeline continues automatically
- Modify blog content that was already exported — that is the domain of earlier pipeline skills
