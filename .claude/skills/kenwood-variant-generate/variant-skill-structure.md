# Variant Skill Structure Specification

Common input/output contract for all variant generation skills -- both the orchestrating skill (`generate-variants`) and standalone per-platform skills (S19--S23).  Every variant skill follows this structure.

---

## Input

Content piece ID, provided either by:
- Skill injection registry prompt: `Run /generate-variants for content piece #{entity_id}`
- Direct operator request: "Generate a LinkedIn variant for content piece 42"

---

## Social Variant Strategy: Teaser-First

**Every social variant exists to drive clicks to the website.**  The blog post is the full argument.  Social variants are teasers that create enough curiosity, tension, or FOMO that the reader needs to click through to get the resolution.

This applies to all social platforms: LinkedIn, X, BlueSky, Instagram.  It does NOT apply to WordPress, which is a full article cross-post for SEO surface expansion.

**What "teaser" means in practice:**
- **Hook with personal experience.**  Open with a scene, an observation, or a moment that pulls the reader in.  The hook earns attention through specificity, not through promising a list of tips.
- **Build tension without resolving it.**  Establish what happened, why it mattered, hint at what you found.  Do NOT give away the conclusion, the framework, the specific steps, or the full payoff.
- **Create the information gap.**  The reader should finish the post knowing there is something valuable in the full article that they cannot get from the social post alone.  "I wrote up what worked and what didn't" implies specific experiments the reader wants to see.  "Here are the five things that worked" gives them away.
- **The link is the resolution.**  On platforms where the link is in the post (X, BlueSky), it completes the tension.  On LinkedIn, the first-comment link does.  On Instagram, "link in bio" does.  The social post creates the question; the blog answers it.

**What teaser does NOT mean:**
- Vague, contentless hooks that promise without substance.  The post must be interesting on its own.  The reader should feel they got a good moment AND want more.
- Clickbait.  The post honestly represents what the blog contains.  The FOMO comes from withholding depth, not from manufacturing urgency.

**Platform-specific teaser expression:**

| Platform | Teaser shape | Budget |
|----------|-------------|--------|
| LinkedIn | 2-3 flowing paragraphs: scene, pivot, tease | 600-1,000 chars |
| X thread | Tension building across 3-5 posts; final post link is the resolution | 280 chars/post |
| X standalone | One sharp observation that creates curiosity + link | 280 chars total |
| BlueSky thread | Conversational curiosity building; link resolves | 300 chars/post |
| BlueSky post | Thinking-out-loud observation + link | 300 chars total |
| Instagram | Behind-the-scenes moment; "link in bio" | 2,200 chars max |
| WordPress | Full article (NOT a teaser; SEO cross-post) | Unlimited |

---

## Source Read

Read the content piece before generating any variant.

| Command | Purpose |
|---------|---------|
| `cli-kenwood content get <id>` | Metadata: title, status, slug, content_type, tags, summary, meta_description, venture, project |
| `cli-kenwood content body <id>` | Full markdown body |
| `cli-kenwood storyboards list --content-id <id>` | Storyboard with frame list and image paths (if storyboard exists) |

**Gate check:** Content piece must be in `published` status.  If not, report to operator and stop.

---

## Image Discovery and Resolution

Images are stored in the **Storyboard** system, not on the content piece itself.  A storyboard has one or more frames, each with an `image_path`.

### Discovery command

```bash
cli-kenwood storyboards list --content-id <id>
```

If the command returns a storyboard with frames, use the frame `image_path` values.  If it returns no storyboard or no frames, the content piece has no images.

### `featured_image_ref` semantics

The `featured_image_ref` field in `format_metadata` controls whether the publisher attaches an image.  The publisher's `resolve_post_image()` function reads this field.  **The semantics of the value matter:**

| Value | Meaning | Publisher behaviour |
|-------|---------|---------------------|
| `"/path/to/image.png"` | Use this specific image | Downloads and attaches the image |
| `null` (key present, value null) | **Explicit opt-out — no image** | Returns immediately, no fallback |
| Key absent | No image decision made | Falls through to storyboard fallback |

**When to set each value:**
- **Path string:** Storyboard exists and has completed frames.  Select the appropriate frame's `image_path`.
- **Null:** The platform constraint says text-only for this variant type (e.g., X standalone, BlueSky post), or discovery found no images and the operator confirmed text-only.
- **Never omit the key** for platforms that use images.  An absent key means the publisher's fallback chain decides, which can attach unexpected images.

### Failure escalation

If `cli-kenwood storyboards list` fails (command error, no storyboard found, all frames have `generation_status != complete`):

1. **Do not assume "no image" and continue.**  The content piece may have images through a path you haven't found.
2. **Report to Sam:** "Image discovery failed for content piece <id>: <reason>.  Proceed as text-only, or point me to the image?"
3. **Wait for confirmation** before setting `featured_image_ref: null`.

---

## Blog URL Construction

**CRITICAL — the Kenwood `slug` and the website URL slug are different.**

| Field | Example | Use for |
|-------|---------|---------|
| `slug` (from CLI) | `2026-04-03-was-it-all-just-a-dream-11` | Internal Kenwood identification only |
| `url_slug` (from CLI) | `was-it-all-just-a-dream` | Website URL path |
| `blog_url` (from CLI) | `https://otagelabs.com/blog/was-it-all-just-a-dream` | Canonical URL, CTA links, blog links |

`cli-kenwood content get <id>` returns all three fields.  **Always use `blog_url` (or `url_slug`) when constructing links for variants.**  Never construct a blog URL from the `slug` field — it contains a date prefix and database ID suffix that produce broken 404 links on the website.

For platform-specific links, append UTM parameters to `blog_url`:
- LinkedIn comment: `{blog_url}?utm_source=linkedin&utm_medium=social`
- WordPress canonical: `{blog_url}` (no UTM — it's a canonical reference)
- X/Twitter: `{blog_url}?utm_source=twitter&utm_medium=social`
- BlueSky: `{blog_url}?utm_source=bluesky&utm_medium=social`
- Instagram link-in-bio: `{blog_url}?utm_source=instagram&utm_medium=social`

---

## Variant Check

Before generating, check for existing variants:

```bash
cli-kenwood variants list --content-id <id>
```

If variants exist for the target platform(s), report which platforms already have variants and ask the operator how to proceed.  Default: skip platforms with existing `approved` or `deployed` variants, regenerate for platforms with `rejected`, `cancelled`, or `failed` variants.

---

## Variant Write-Back

Write each variant immediately after generation.  Do not batch.

```bash
cli-kenwood variants create \
  --content-id <id> \
  --platform <slug> \
  --variant-type <type> \
  --title "<title>" \
  --body "<body>" \
  --format-metadata '<json>'
```

| Parameter | Values |
|-----------|--------|
| `platform` | `linkedin`, `twitter-x`, `wordpress`, `bluesky`, `instagram` |
| `variant-type` | Platform-dependent: `post`, `thread`, `standalone`, `article`, `caption` |
| `body` | The variant content as readable text (used for review UI display) |
| `format-metadata` | JSON object with platform-specific metadata (see format_metadata schemas below) |

Created variants are in `draft` status.

---

## MC Surfacing

Surface each variant in Mission Control immediately after creation:

```bash
cli-kenwood mc focus --entity-type content_variant --entity-id <variant_id>
```

For the first entity interaction in a session, include `--navigate` to switch the workspace view:

```bash
cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate
```

See `.claude/rules/mc-surfacing.md` for full surfacing rules.

---

## Output

One or more ContentVariant records in `draft` status, written via CLI.  Each variant has:
- `body`: Readable text for review
- `format_metadata`: Platform-specific structured data for deployment
- `platform_id`: Links to the target platform
- `variant_type`: Platform-specific variant type
- `status`: `draft` (ready for operator review)

---

## format_metadata Schemas (by platform)

Each platform defines its own `format_metadata` structure.  The schemas are documented in the companion software PRDs.  This specification references them -- it does not duplicate them.

| Platform | Variant Type | Schema Reference |
|----------|-------------|-----------------|
| LinkedIn | `post` | S13 FR2 |
| X/Twitter | `thread` | S14 FR3 |
| X/Twitter | `standalone` | S14 FR4 |
| WordPress | `article` | S15 FR2 |
| BlueSky | `post` | S16 FR3 |
| BlueSky | `thread` | S16 FR4 |
| Instagram | `caption` | S17 FR2 |

### Key fields across platforms

- **`char_count`** / **`per_post_char_counts`**: Character counts for validation
- **`utm_params`**: UTM tracking parameters (`utm_source` = platform name, `utm_medium` = social/blog)
- **`featured_image_ref`**: Path to storyboard or featured image
- **`hashtags`**: Platform-appropriate hashtag arrays (Instagram only -- LinkedIn has zero hashtags under 360Brew)
- **`posts`**: Pre-structured thread posts array (X thread, BlueSky thread)
- **`is_thread`**: Boolean flag for thread variants
- **`thread_count`**: Number of posts in thread

---

## Voice and Writing Guidelines

**Voice is non-negotiable.** All generated variant content must sound like Sam, not like a content mill.

**Mandatory reads before generating any variant:**
1. `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's conversational voice guide.  This is the voice benchmark.
2. `.claude/rules/writing.md` — editorial rules, banned words, LLM pattern avoidance, double spaces.

**Mechanical character scan (mandatory — runs BEFORE the voice gate):**

The voice gate below is qualitative; this scan is binary.  Run it first because an LLM can pass the qualitative voice gate while leaving Unicode artifacts in the prose, and those artifacts (em dashes, smart quotes, ellipsis characters) are LLM authorship tells that signal AI authorship to readers regardless of how good the writing is.

Before running the voice gate, search the variant body character-by-character for each forbidden pattern.  Any single hit is an automatic rewrite — no judgement call, no exceptions.

| Pattern | Forbidden | Substitute |
|---|---|---|
| `—` (em dash, U+2014) | always | comma, semicolon, or sentence break |
| `–` (en dash, U+2013) | always | hyphen `-` for numeric ranges only; otherwise comma or sentence break |
| ` -- ` (double-hyphen as em-dash substitute) | always | comma, semicolon, or sentence break |
| `"` `"` (smart double quotes, U+201C / U+201D) | always | straight ASCII `"` |
| `'` `'` (smart single quotes / apostrophes, U+2018 / U+2019) | always | straight ASCII `'` |
| `…` (ellipsis character, U+2026) | always | three ASCII periods `...` |

**Scope of the scan -- the WHOLE output surface, not just variant body.**

The scan applies to every string the variant manager produces in a session: variant body, draft presentations to the operator, hook drafts shown for review, angle/fidelity discussions, post-correction apologies, status reports.  The rule governs the persona's entire writing surface, not just the artifact published to Kenwood.

Why: the variant manager's chat narration is part of her voice compass.  An apology about em dashes that contains em dashes proves the rule is not internalised, and a manager who can't keep dashes out of a 200-word message has no calibrated instrument to apply the rule to a variant.  Surface-wide compliance is how the calibration is built and maintained.

**How to run:** before sending any message to the operator, and before invoking `cli-kenwood variants create`, scan the full output string for each pattern (a literal substring search is sufficient).  If any pattern is present, rewrite the offending sentences using the substitute and re-scan.  Do not present a draft, pitch a hook, or call `cli-kenwood variants create` until the scan returns clean for every pattern across the entire message.

**Why both gates exist:** the mechanical scan catches LLM tells the voice gate cannot detect.  The voice gate catches voice drift the mechanical scan cannot detect.  Both must pass.

---

**Voice self-check gate (8-point, all must pass before writing a variant to Kenwood):**
1. Does the variant preserve at least one named reference from the source (agent names, product names, project names)?  **Yes/No**
2. Does the variant use specific terms from the source rather than generic substitutes?  **Yes/No**
3. Does the variant include at least one vulnerability or honest admission from the source (where the platform's format allows)?  **Yes/No**
4. Does the closer create FOMO or leave the reader wanting more (tease, open question, or honest admission) rather than delivering a thesis statement or neat conclusion?  **Yes/No**
5. Does the variant contain at least two different sentence lengths in sequence?  **Yes/No**
6. Does the variant stay in scene — characters acting, things happening — rather than pivoting to advice, prescriptions, or abstract principles?  On social platforms, default to scene over instruction even when the source uses instruction mode.  When compressing for shorter formats, find a sharper angle from the story; don't summarise the story into a principle.  **Yes/No**
6b. Does the variant linger in description where the point is how something feels, rather than compressing into tight parallel lists?  Flowing description ("understand the detail and the nuance of a specific requirement") sits in the moment; tight lists ("the commit, the branch, the review") sprint past it.  Are metaphors grounded in concrete, physical details rather than left as abstractions?  **Yes/No**
7. Read every sentence aloud.  Would Sam say each one to someone over a beer, or does it sound written for a stage?  Any sentence that sounds performed — punchy, quotable, designed — gets rewritten in plain language.  **Yes/No**
8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source content piece?  Cross-check: if the source says "twelve decisions, two lost," the variant cannot say "ten decisions, all lost."  Inflating, rounding, or inverting facts for hook impact is fabrication and an automatic fail regardless of how well the rest of the variant reads.  **Yes/No**

Any failure means rewrite, not ship.  A variant that passes platform mechanics but fails voice is not ready.

**Source content is a voice reference.** The source content piece has already been written in Sam's voice.  Treat it as both the argument source AND the voice benchmark.  Compress and adapt for the platform while preserving voice texture: named references, vulnerability markers, observation-over-verdict framing, and closer style.

---

## Platform Constraints

Each platform has a co-located constraint file in `constraints/` that defines the full set of rules for that platform/variant type.  Read the relevant constraint file before generating each variant.

```
.claude/skills/kenwood-variant-generate/constraints/
+-- linkedin.md
+-- twitter-thread.md
+-- twitter-standalone.md
+-- wordpress.md
+-- bluesky-post.md
+-- bluesky-thread.md
+-- instagram.md
```

Each constraint file is self-contained -- read it independently, no cross-references needed.
