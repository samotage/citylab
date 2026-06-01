# WordPress Article Constraints

Platform: WordPress
Variant type: `article`
Platform slug: `wordpress`

---

## Character Limits and Format Rules

- **No character limit** on the body -- WordPress articles carry full article depth.
- **SEO title:** 50--65 characters.  MUST differ from the source content piece title.  Target complementary search queries to capture additional search surface.
- **Meta description:** 150--160 characters, search-optimised.  Must target different search queries than the source post's meta description.
- **Body format:** Markdown.  The `WordPressPublisher` renders markdown to HTML for publishing.

---

## Structural Requirements

This is an adaptation, not a compression.  The full article carries over with SEO-appropriate framing.

1. **Attribution** at the article top: "Originally published at [otageLabs](canonical_url)."  This is injected by the publisher from `format_metadata.canonical_url`.
2. **SEO-reframed title and opening.**  The WordPress title and opening paragraph may differ from the source to target WordPress.com discovery readers and different search queries.
3. **Full article body.**  The substance is the same article, potentially with audience reframing for WordPress.com readers who discover the piece through search or the WordPress.com reader.
4. **Source images, categories, and tags** carry over from the content piece.

---

## Voice: Sam's Full Voice, WordPress Audience

**Mandatory pre-read:** Before generating any WordPress variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.

**The source content is the voice reference.**  WordPress is cross-publishing, not rewriting.  The source article was written in Sam's voice.  The WordPress variant preserves that voice with minimal audience reframing.  This is the one platform where "match the source" is almost literally the instruction.

**Voice rules (non-negotiable):**
- Preserve ALL named references from the source.  Every agent name, product name, and project name stays.  WordPress is full-depth — there is no compression excuse for stripping specificity.
- Preserve vulnerability markers.  If the source contains honest admissions, uncertainties, or "I don't know" moments, they survive into the WordPress version.
- Preserve the closer.  If the source ends with an open question, the WordPress variant ends with the same open question (or a closely related one).  Do not "tidy up" the closer into a thesis statement.
- Audience reframing is subtle — slightly more accessible for first-time readers, not a complete voice transplant.  The article should be recognisably the same piece by the same person.
- Same first-person voice ("I"), same directness, same practitioner grounding.
- Follow `.claude/rules/writing.md` for banned words and voice rules.
- Double space after every sentence-ending full stop in the variant body (markdown).  Note: double spaces collapse in published HTML output — this is a known limitation.  Enforce in the variant body regardless.

**WordPress anti-convergence (AI-average patterns to avoid):**
- Stripping named references "for a wider audience" — the names ARE the authenticity
- Smoothing out sentence-rhythm variation into uniform paragraph length
- Replacing the source's closer with a neater conclusion
- Adding SEO-bait intros: "In this article, you'll learn..."
- Over-reframing: the WordPress variant should read like the same person wrote it, not like it was "adapted" by a content team

---

## CTA Conventions

- No explicit CTA needed in the body -- the attribution link at the top serves as the CTA to the source.
- The article should stand on its own.  Do not end with "read the full version" since this is the full version.

---

## Hashtag Rules

- WordPress does not use hashtags.
- Tags from the source content piece are mapped to WordPress categories and tags by the publisher.

---

## Image Handling

- Featured image from the source content piece (storyboard or featured image).
- Store the image path in `format_metadata.featured_image_ref`
- The `WordPressPublisher` uploads the featured image and sets it as the post's featured media.

---

## UTM Parameter Requirements

The canonical URL (attribution link) should not include UTM parameters -- it is a canonical reference, not a tracking link.

For any other links within the article body that point to otageLabs:
- `utm_source=wordpress`
- `utm_medium=blog`

Store in `format_metadata.utm_params` as `{"utm_source": "wordpress", "utm_medium": "blog"}`.

---

## Anti-Patterns

1. **Summarising the source article.**  WordPress variants are full-depth adaptations.  Do not shorten or compress the original content.
2. **Identical title and meta description.**  The WordPress version must target different search queries than the source to capture additional search surface.  Same title = wasted SEO opportunity.
3. **Missing attribution.**  Every WordPress variant must acknowledge the source via "Originally published at otageLabs" with a canonical link.
4. **Missing canonical URL.**  Without the canonical URL, search engines may treat this as duplicate content, penalising both the source and the WordPress version.
5. **Over-reframing.**  The audience shift for WordPress is subtle -- not a complete rewrite.  The argument and structure should be recognisably the same article.
6. **Adding WordPress-specific fluff.**  Do not pad the article with SEO-bait paragraphs, keyword stuffing, or "In this article, you'll learn..." intros.

---

## SEO Rules

- **Title:** 50--65 characters for optimal search display.  MUST differ from the source post title -- if the source targets "production AI debugging," the WordPress variant might target "fix AI agents after deployment."
- **Meta description:** 150--160 characters.  Include the primary target keyword naturally.  MUST target different search intent from the source post's own meta description.
- **Keywords:** Identify 2--3 target keywords that complement (not duplicate) the source post's keywords.
- **Opening paragraph:** The primary target keyword should appear within the first 100 words.

---

## format_metadata Output Specification

Each WordPress variant must include a `format_metadata` JSON object with these fields:

```json
{
  "seo_title": "<string, 50-65 chars, different from source title>",
  "meta_description": "<string, 150-160 chars, different search intent>",
  "canonical_url": "<string, use blog_url from cli-kenwood content get>",
  "featured_image_ref": "<string, storyboard image path or null>",
  "utm_params": {"utm_source": "wordpress", "utm_medium": "blog"},
  "word_count": "<int, total word count of variant body>",
  "source_content_piece_id": "<int, ID of the source content piece>"
}
```

**CRITICAL — canonical_url construction:**  Use the `blog_url` field from `cli-kenwood content get <id>`.  This is the correct website URL (e.g. `https://otagelabs.com/blog/was-it-all-just-a-dream`).  **Do NOT use the Kenwood `slug` field** — that is the internal slug with date prefix and ID suffix (e.g. `2026-04-03-was-it-all-just-a-dream-11`) and produces broken links.

---

## Example

Source title: "Why agents break in production"

WordPress variant title: "How to debug AI agents that fail after deployment" (55 chars, complementary search query)

Meta description: "AI agents pass testing but fail in production.  The gap between demo and deployment hides three failure modes every team misses." (155 chars)

Body: "Originally published at [otageLabs]({blog_url from cli-kenwood output})." at the top, followed by the complete article with reframed opening for WordPress.com discovery readers.
