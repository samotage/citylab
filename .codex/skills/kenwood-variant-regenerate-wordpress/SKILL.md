---
name: regenerate-wordpress-variant
description: Regenerate a WordPress article variant with SEO-adapted title, meta description,
  and attribution.
metadata:
  short-description: Regenerate a WordPress article variant with SEO-adapted title,
    meta description, and attribution.
---

# Skill: Regenerate WordPress Variant

Regenerate a single WordPress article variant independently of the full orchestration flow.  For cases where a rejected variant needs a fresh SEO angle, source content changed, or WordPress-only generation is needed.

**Trigger:** Skill injection "Regenerate" button on rejected/failed/cancelled WordPress variants, or operator says "regenerate WordPress variant for content piece <id>."

## References

- **Platform constraints:** `../kenwood-variant-generate/constraints/wordpress.md` — all WordPress rules, SEO rules, and format_metadata schema
- **Shared structure:** `../kenwood-variant-generate/variant-skill-structure.md` — input/output contract, voice self-check gate
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's conversational writing voice (mandatory read before generating)
- **Writing rules:** `.claude/rules/writing.md` — banned words, double spaces, voice rules
- **MC surfacing:** `.claude/rules/mc-surfacing.md` — when and how to surface entities

---

## Phase 1: Read Source

1. Read content piece metadata: `cli-kenwood content get <id>`
2. Read full content body: `cli-kenwood content body <id>`
3. Read storyboard images: `cli-kenwood storyboards list --content-id <id>`.  WordPress articles use `featured_image_ref` for the post's featured media.  If no storyboard or no completed frames, report to Sam before proceeding.  See `variant-skill-structure.md` § Image Discovery and Resolution.
4. Read the voice reference: `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  This is non-negotiable editorial law.  Internalise Sam's voice markers before generating.
5. Note the source post's title, slug, summary, and any existing meta description
6. Check for existing WordPress variants: `cli-kenwood variants list --content-id <id>`
7. Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate`

**Gate:** Content piece must be in `published` status.  If not, report and stop.

If existing WordPress variants exist, note their bodies, format_metadata, and statuses.  Rejected/failed/cancelled variants inform the SEO angle differentiation in Phase 2.

---

## Phase 2: Generate

1. Read the WordPress constraint file from `../kenwood-variant-generate/constraints/wordpress.md`
2. If regenerating after rejection: read the rejected variant's body and format_metadata to understand the previous SEO angle.  Deliberately choose different target keywords and a different title angle.
3. Identify 2--3 complementary search keywords (different from source post keywords and any previous variant's keywords).
4. Generate SEO title targeting those keywords (50--65 characters).
5. Generate meta description targeting different search intent (150--160 characters).
6. Construct canonical URL using the `blog_url` field from `cli-kenwood content get <id>`.  **Do NOT use the Kenwood `slug` field** — it contains a date prefix and ID suffix that produce broken links.
7. Adapt the article body: prepend attribution, reframe opening for WordPress.com discovery readers, make references self-contained.  This is adaptation, not rewriting — same argument, same evidence.
7b. **Mechanical character scan (mandatory before voice gate).**  Scan the variant body for `—` (em dash), `–` (en dash), ` -- ` (double-hyphen), smart quotes (`"` `"` `'` `'`), and `…` (ellipsis char).  Any single hit is an automatic rewrite — these are LLM authorship tells.  Use straight ASCII substitutes (commas/semicolons/sentence breaks for dashes; `"` and `'` for quotes; `...` for ellipsis).  Re-scan after rewriting.  Do NOT proceed to the voice gate until clean.  Full pattern table in `../kenwood-variant-generate/variant-skill-structure.md`.

8. **Voice self-check (7-point gate).**  All must pass before writing:
   1. Preserves ALL named references from the source (full-depth, no compression excuse)?  2. Uses specific terms, not generic substitutes?  3. Preserves vulnerability markers and honest admissions?  4. Closer matches the source's closer style (open question or honest admission)?  5. Sentence-length variation preserved from source?  6. Stays in narrative mode where the source tells a story?  WordPress articles have runway for instructional sections the source earns, but narrative passages must stay narrative.  7. Every sentence passes the coffee test — would Sam say it over a beer?  8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source?  Inflating or inverting facts is fabrication and an automatic fail.  Any failure means rewrite.
9. Present the SEO metadata (title, meta description, target keywords) to Sam for confirmation.  Wait for approval.
10. Construct `format_metadata` JSON per the constraint file's output specification.
11. Write the variant:
    ```bash
    cli-kenwood variants create --content-id <id> --platform wordpress --variant-type article --title "WordPress article" --body "<adapted body>" --format-metadata '<json>'
    ```
11. Surface variant and refresh content piece:
    ```bash
    cli-kenwood mc focus --entity-type content_variant --entity-id <variant_id>
    cli-kenwood mc focus --entity-type content_piece --entity-id <id>
    ```

---

## Phase 3: Report

1. Report to Sam: variant created, SEO title, target keywords, word count, canonical URL
2. Remind Sam to review SEO metadata in the variant review UI

---

## Hard Constraints

1. SEO title MUST differ from source post title.  50--65 characters.
2. Meta description MUST target different search intent from source.  150--160 characters.
3. Canonical URL MUST point to the otageLabs source post.
4. Attribution MUST appear at the top of the article body.
5. Body is adaptation, not rewriting.  Same argument, same evidence, reframed entry point.
6. **Voice is non-negotiable.**  Read `voice.md` before generating.  Apply the 8-point voice self-check gate before writing.  `.claude/rules/writing.md` banned words, double spaces, and LLM pattern avoidance enforced.
7. When regenerating after rejection, MUST use different target keywords and a different SEO title angle.
8. Do not duplicate constraint definitions -- reference the shared constraint file only.
