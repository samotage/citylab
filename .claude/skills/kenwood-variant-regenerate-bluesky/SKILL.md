---
name: regenerate-bluesky-variant
description: "Regenerate BlueSky variants (post + thread) for a published content piece."
---

# Skill: Regenerate BlueSky Variant

Regenerate BlueSky variants independently of the full orchestration flow.  BlueSky produces two variant types: a post (single conversational take) and a thread (3--5 post reply chain).  The tone is conversational and community-oriented -- warmer than X, less formal than LinkedIn.

**Trigger:** Skill injection "Regenerate" button on rejected/failed/cancelled BlueSky variants, or operator says "regenerate BlueSky variant for content piece <id>."

## References

- **Post constraints:** `../kenwood-variant-generate/constraints/bluesky-post.md`
- **Thread constraints:** `../kenwood-variant-generate/constraints/bluesky-thread.md`
- **Shared structure:** `../kenwood-variant-generate/variant-skill-structure.md` — input/output contract, voice self-check gate
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's conversational writing voice (mandatory read before generating)
- **Writing rules:** `.claude/rules/writing.md` — banned words, double spaces, voice rules
- **MC surfacing:** `.claude/rules/mc-surfacing.md`

---

## Phase 1: Read Source

1. Read content piece metadata: `cli-kenwood content get <id>`
2. Read full content body: `cli-kenwood content body <id>`
3. Read storyboard images: `cli-kenwood storyboards list --content-id <id>`.  Thread variants use `featured_image_ref` on post 1; standalone posts are text-only (set `featured_image_ref: null` or omit).  If no storyboard or no completed frames and generating a thread, report to Sam before proceeding.  See `variant-skill-structure.md` § Image Discovery and Resolution.
4. Read the voice reference: `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  This is non-negotiable editorial law.  Internalise Sam's voice markers before generating.
5. Check for existing BlueSky variants: `cli-kenwood variants list --content-id <id>`
6. Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate`

**Gate:** Content piece must be in `published` status.  If not, report and stop.

If existing BlueSky variants exist, note their bodies, statuses, and variant types (post/thread).  Rejected/failed/cancelled variants inform angle and tonal differentiation in Phase 2.

**Selective regeneration (FR6):** If only one variant type was rejected (post or thread), regenerate only that type unless Sam requests both.  If both were rejected, regenerate both.

---

## Phase 2: Generate

1. Read both BlueSky constraint files: `../kenwood-variant-generate/constraints/bluesky-post.md` and `../kenwood-variant-generate/constraints/bluesky-thread.md`
2. If regenerating after rejection: read the rejected variant(s) to understand previous angles.  Choose a different angle or tonal approach.  On BlueSky, "different tonal approach" is a valid change -- same insight from a curious perspective instead of a declarative one.
3. Identify the thread angle (conversational exploration that works through an idea across 3--5 posts).
4. Identify the post angle (single conversational take).  Post and thread angles may overlap on BlueSky -- the post can be a compressed version of the thread's exploration because the conversational tone carries across both.
5. Present both angles to Sam for confirmation.  Wait for approval.
6. Generate the thread variant following thread constraints.  No numbering in post text.  Each post must be at or under 300 characters.
6b. **Mechanical character scan (mandatory before voice gate, applies to BOTH the thread AND the post).**  Scan each variant body for `—` (em dash), `–` (en dash), ` -- ` (double-hyphen), smart quotes (`"` `"` `'` `'`), and `…` (ellipsis char).  Any single hit is an automatic rewrite — these are LLM authorship tells.  Use straight ASCII substitutes (commas/semicolons/sentence breaks for dashes; `"` and `'` for quotes; `...` for ellipsis).  Re-scan after rewriting.  Do NOT proceed to the voice gate until clean.  Full pattern table in `../kenwood-variant-generate/variant-skill-structure.md`.

7. **Voice self-check (7-point gate)** on the thread variant.  All must pass before writing:
   1. Preserves at least one named reference from the source?  2. Uses specific terms, not generic substitutes?  3. Includes vulnerability or honest admission?  4. Closer passes punchline test?  5. Contains sentence-length variation?  6. Stays in scene rather than pivoting to advice or abstract principles?  Compress by finding a sharper story angle, not by abstracting.  7. Every sentence passes the coffee test — would Sam say it over a beer?  8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source?  Inflating or inverting facts is fabrication and an automatic fail.  Any failure means rewrite.
8. Construct thread `format_metadata` per the constraint file's output specification.
9. Write thread variant:
   ```bash
   cli-kenwood variants create --content-id <id> --platform bluesky --variant-type thread --title "BlueSky thread" --body "<full thread text>" --format-metadata '<json>'
   ```
9. Surface thread and refresh content piece:
   ```bash
   cli-kenwood mc focus --entity-type content_variant --entity-id <thread_variant_id>
   cli-kenwood mc focus --entity-type content_piece --entity-id <id>
   ```
11. Generate the post variant following post constraints.  Must be at or under 300 characters.
12. **Voice self-check** on the post.  Checks 1, 2, 5, 6, and 7 must pass (vulnerability and closer checks are less applicable at 300 chars).  Any failure means rewrite.
13. Construct post `format_metadata` per the constraint file's output specification.
14. Write post variant:
    ```bash
    cli-kenwood variants create --content-id <id> --platform bluesky --variant-type post --title "BlueSky post" --body "<post text>" --format-metadata '<json>'
    ```
13. Surface post and refresh content piece:
    ```bash
    cli-kenwood mc focus --entity-type content_variant --entity-id <post_variant_id>
    cli-kenwood mc focus --entity-type content_piece --entity-id <id>
    ```

---

## Phase 3: Report

1. Report both variants: thread (post count, hook preview) and post (full text preview)
2. Remind Sam to review in the variant review UI

---

## Hard Constraints

1. Per-post character count MUST be at or under 300.
2. Thread posts MUST NOT include numbering (no "1/", "2/").
3. No hashtags anywhere in BlueSky content.
4. Tone MUST be conversational, not presentational.  If a BlueSky variant reads like an X variant, it has failed.
5. **Voice is non-negotiable.**  Read `voice.md` before generating.  Apply voice self-check gate before writing each variant.  `.claude/rules/writing.md` banned words, double spaces, and LLM pattern avoidance enforced.
6. When regenerating after rejection, MUST use a different angle or tonal approach from the rejected variant(s).
7. Selective regeneration: regenerate only the rejected variant type unless Sam requests both.
8. Do not duplicate constraint definitions -- reference the shared constraint files only.
