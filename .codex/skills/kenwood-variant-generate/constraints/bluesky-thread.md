# BlueSky Thread Constraints

Platform: BlueSky
Variant type: `thread`
Platform slug: `bluesky`

---

## Character Limits and Format Rules

- **Thread length:** 3--5 posts
- **Per-post character limit:** 300 characters each.  Hard ceiling enforced by the AT Protocol.
- **No numbering.**  BlueSky threads do not use `1/`, `2/` conventions.  The tone is conversational, not presentational.  The reply-chain structure indicates thread continuity.
- **Thread body field:** The `body` field on the variant contains the full readable text (all posts concatenated).  The `format_metadata.posts` array contains the individual per-post text for publishing.
- **Links:** Rendered as AT Protocol facets (clickable in the BlueSky app).  The publisher generates facets automatically.

---

## Structural Requirements

The thread is a teaser.  It builds conversational curiosity without delivering the full argument.  The blog link in the final post is the resolution.

1. **Post 1 (hook):** Must work as a standalone post.  BlueSky surfaces thread starters in feeds -- the hook determines whether anyone taps through to the rest.
2. **Posts 2--4 (body):** One idea per post.  Each post should feel like the next thing you would say in conversation.  Build curiosity and tension.  Hint at what was found, but do NOT deliver the conclusion, the framework, or the specific steps -- those live in the blog post.
3. **Final post:** Links to the full article with UTM parameters.  The link resolves the curiosity the thread built.  Frame naturally: "Wrote about this in more detail:" -- not as a request.

The thread should read like a conversation unfolding that leaves the reader wanting more, not a structured argument being presented and resolved.

---

## Voice: Sam Thinking Out Loud, Threaded

**Mandatory pre-read:** Before generating any BlueSky thread variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.

**The source content is a voice reference, not just an argument to mine.**  The source piece has already been written in Sam's voice.  Decompose the argument into conversational posts while preserving voice texture; named references, vulnerability, observation-over-verdict.

A BlueSky thread is a conversation unfolding that leaves the reader wanting more.  Each post is the next thing Sam would say, building curiosity without delivering the full payoff.  The blog link resolves it.

**Voice rules (non-negotiable):**
- Preserve at least one named reference from the source.  Agent names, product names, specific details — the thread must be grounded in Sam's specific experience.
- Thinking-out-loud energy: each post feels like the next thought, not the next section.  "And then this happened" is conversational.  "Furthermore, the following occurred" is a paper.
- Vulnerability works.  "I don't know if this scales" is stronger than "This approach has certain limitations."
- No numbering.  BlueSky threads use reply-chain structure for continuity.  Numbering signals cross-posting from X.
- **Observation over verdict.**  Even in a thread, Sam observes rather than pronounces.  "I noticed the decisions weren't in the build" is an observation.  "Teams need better handoff processes" is a verdict.
- **The post before the link should feel like a natural finish.**  An honest admission, a trailing observation, or a question; not a thesis statement wrapping up the argument.
- Dry humor: observations that land because they're true.
- **Concrete metaphors.**  Ground metaphors in physical, tangible details — "a hundred kilometers an hour" not "highway speed."  Colloquial phrases do real work.
- **Sharp gear shifts.**  Use deliberate breaks between ideas.  An abrupt scene change is more Sam than a smooth transition.
- First person ("I"), contractions, sentence fragments all work.
- Vary post length.  A short two-sentence post between longer ones creates rhythm.
- Follow `.claude/rules/writing.md` for banned words and voice rules.
- Double space after every sentence-ending full stop.

**BlueSky thread anti-convergence (AI-average patterns to avoid):**
- Presentation-style threading: "First... Next... Finally..." — this is a conversation, not a deck
- Uniform post length across all posts
- Authority positioning in the hook: "After years of experience, I've found..."
- Generic observations with no source-specific details
- Cross-posted from X: same text with numbering removed but X's compression and tone intact
- Engagement farming in the final post

---

## CTA Conventions

- The final post contains the blog link with UTM parameters.
- Frame naturally: "Longer version here:" or "Wrote about this in detail:"
- Do not beg for engagement.  BlueSky's culture penalises engagement-farming.

---

## Hashtag Rules

- Zero hashtags is the default for BlueSky threads.
- If a hashtag is genuinely part of an ongoing community conversation, one hashtag maximum in the final post.

---

## Image Handling

- Featured image on post 1 only.  No images on subsequent posts.
- Store the image path in `format_metadata.featured_image_ref`
- The publisher uploads the image as an AT Protocol blob and attaches it to the first post.
- If no storyboard image is available, the thread publishes as text-only.

---

## UTM Parameter Requirements

The link in the final post must include UTM parameters:
- `utm_source=bluesky`
- `utm_medium=social`

Store in `format_metadata.utm_params` as `{"utm_source": "bluesky", "utm_medium": "social"}`.

**CRITICAL — URL construction:**  Build the blog link from the `blog_url` field in `cli-kenwood content get <id>`, then append `?utm_source=bluesky&utm_medium=social`.  **Do NOT use the Kenwood `slug` field** — it contains a date prefix and ID suffix (e.g. `2026-04-03-my-post-11`) that produce broken links.  The correct URL uses only the title slug (e.g. `https://otagelabs.com/blog/my-post`).

---

## Anti-Patterns

1. **Using 1/, 2/ numbering.**  BlueSky threads do not use this convention.  It signals cross-posting from X.
2. **Posts exceeding 300 characters.**  The AT Protocol enforces this strictly.  Each post must independently fit.
3. **Lecture-style threading.**  BlueSky threads that read like a presentation feel out of place.  Each post should feel like the next thought in a conversation.
4. **Copying the X thread.**  BlueSky has a different culture and character limit (300 vs 280).  Write for this platform specifically.
5. **Authority positioning.**  "As someone who has been doing X for years" is broadcast energy.  Share the insight directly.
6. **Engagement farming.**  "Boost this thread" or "Reply with your thoughts" is anti-BlueSky culture.
7. **Thread padding.**  If the argument fits in 3 posts, do not stretch to 5.

---

## Example Output

Thread body (all posts concatenated for review):

```
I keep debugging the same pattern in production AI agents.  It works in testing.  It breaks at 3am on a Saturday.  Every time.

The gap isn't the model.  It's the assumptions.  Context windows that work in testing overflow with real conversation history.  Retry logic that was never tested under actual rate limits enters infinite loops.

Not more testing.  Better testing.  The failure modes that only show up under production conditions -- rate limits, empty inputs, concurrent sessions -- are the ones that matter.

Wrote about the full pattern here: https://otagelabs.com/blog/agent-debugging?utm_source=bluesky&utm_medium=social
```

format_metadata.posts:

```json
[
  {"index": 1, "text": "I keep debugging the same pattern in production AI agents.  It works in testing.  It breaks at 3am on a Saturday.  Every time."},
  {"index": 2, "text": "The gap isn't the model.  It's the assumptions.  Context windows that work in testing overflow with real conversation history.  Retry logic that was never tested under actual rate limits enters infinite loops."},
  {"index": 3, "text": "Not more testing.  Better testing.  The failure modes that only show up under production conditions -- rate limits, empty inputs, concurrent sessions -- are the ones that matter."},
  {"index": 4, "text": "Wrote about the full pattern here: https://otagelabs.com/blog/agent-debugging?utm_source=bluesky&utm_medium=social"}
]
```

---

## format_metadata Output Specification

The `format_metadata` JSON object for a BlueSky thread variant:

```json
{
  "thread_count": <int, 3-5>,
  "is_thread": true,
  "per_post_char_counts": [<int>, ...],
  "posts": [
    {"index": 1, "text": "..."},
    {"index": 2, "text": "..."}
  ],
  "featured_image_ref": "<path>",
  "utm_params": {"utm_source": "bluesky", "utm_medium": "social"}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `thread_count` | int | Number of posts in the thread.  Must be 3--5. |
| `is_thread` | boolean | Always `true` for thread variants. |
| `per_post_char_counts` | array of int | Character count per post.  Each must be at or under 300. |
| `posts` | array of objects | Per-post structured data for publishing.  `index` is for ordering, not display -- post text must NOT include numbering. |
| `featured_image_ref` | string | Path to the featured image for post 1.  Empty string if no image available. |
| `utm_params` | object | UTM tracking parameters for the blog link in the final post. |
