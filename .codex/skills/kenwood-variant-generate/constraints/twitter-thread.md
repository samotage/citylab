# X Thread Constraints

Platform: X (Twitter)
Variant type: `thread`
Platform slug: `twitter-x`

---

## Character Limits and Format Rules

- **Thread length:** 3--5 posts
- **Per-post character limit:** 280 characters each.  No exceptions.  Each post must independently fit within 280 characters including numbering prefix and any links.
- **Numbering:** Explicit `1/`, `2/`, etc. at the start of each post.  This signals to readers that more content follows.
- **Thread body field:** The `body` field on the variant contains the full readable text (all posts concatenated).  The `format_metadata.posts` array contains the individual per-post text for publishing.

---

## Structural Requirements

The thread is a teaser.  It builds tension and curiosity across posts without delivering the full argument.  The blog link in the final post is the resolution.  The reader should finish the thread wanting more, not feeling satisfied.

1. **Post 1/ (hook):** Must work as a standalone scroll-stopper.  When readers see this in their timeline, they must want to tap through.  The hook is the most important post -- if it doesn't stop the scroll, the thread is invisible.
2. **Posts 2/--4/ (body):** One idea per post.  Each post builds tension or curiosity.  Establish what happened, why it matters, hint at what was found.  Do NOT deliver the conclusion, the framework, or the specific steps -- those live in the blog post.  The reader finishes each body post wanting more.
3. **Final post (link):** Links to the full article with UTM parameters.  The link resolves the tension the thread built.  Frame naturally: "Wrote up what I found:" or "Full story:" -- not "Please read my blog post."  The thread creates the FOMO; the link satisfies it.

---

## Voice: Sam Threading on X

**Mandatory pre-read:** Before generating any X thread variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.

**The source content is a voice reference, not just an argument to mine.**  The source piece has already been written in Sam's voice.  Compress the argument into thread-sized posts while preserving the voice texture.  Compression means fewer words, not vaguer words.

Compressed and punchy, but still recognisably Sam.  The thread teases Sam's argument, not delivers it.  Build enough interest that the reader needs the full post.

**Voice rules (non-negotiable):**
- Preserve at least one named reference from the source per thread.  Agent names, product names, specific numbers — the details that make it Sam's experience, not anyone's.
- Each post earns the next through observation, not through lecture.  "I watched this happen" not "Here's what you need to know."
- Dry humor: observations that happen to be funny because they're true.  Not jokes — truth with timing.
- No hedging.  "This breaks in production" not "This might break in production."
- First person ("I"), contractions, sentence fragments are all fine.
- Vary sentence length across posts.  A short fragment post after a dense observation post creates rhythm.
- **Linger where it counts.**  Even in 280-character posts, one flowing description beats a tight list.  Give the reader a moment to sit in the feeling before moving on.
- **Concrete metaphors.**  Ground metaphors in physical details — "a hundred kilometers an hour" not "highway speed."  Colloquial phrases do real work.
- **Sharp gear shifts.**  Use deliberate breaks between ideas.  An abrupt scene change ("Introduce Agentic Development.") is more Sam than a smooth transition.
- **Observation over verdict.**  Even compressed, Sam observes rather than pronounces.  "I keep debugging the same pattern" is an observation.  "AI agents fail in production" is a verdict.
- **At least one post must carry vulnerability or honest surprise.**  "My first reaction was genuine awe.  Then I checked what got built." fits in 280 characters and keeps Sam's voice alive.
- **The post before the link should feel like a natural finish, not a thesis statement.**  An observation that trails off or lands with quiet honesty, not a punchy summary.
- The final post's link framing must sound like Sam offering a payoff, not a marketer requesting clicks.
- Follow `.claude/rules/writing.md` for banned words and voice rules.
- Double space after every sentence-ending full stop.

**X thread anti-convergence (AI-average patterns to avoid):**
- Every post starting with the same structure (e.g., "The problem is... The solution is... The result is...")
- Genericised details: replacing specific tools/agents/projects with category descriptions
- Lecture-style progression: "First... Second... Third..." instead of observation building on observation
- Hook post that could belong to any AI practitioner's thread
- Uniform post length — all five posts at ~250 characters each is AI-average
- Engagement-bait final post: "What do you think?" tacked on without earning the question

---

## CTA Conventions

The final post contains the CTA:
- Link to the full article with UTM parameters
- Frame as payoff: "Full breakdown:" or "Deep dive:" followed by the link
- Do not beg for engagement.  No "Please RT" or "Like if you agree."

---

## Hashtag Rules

- X threads do not use hashtags.  The content speaks for itself.
- If a hashtag is genuinely part of an ongoing conversation (e.g., a conference hashtag), one hashtag maximum in the final post.

---

## Image Handling

- Featured image attached to post 1/ only.  No images on subsequent posts.
- Store the image path in `format_metadata.featured_image_ref`
- If no storyboard image is available, the thread publishes as text-only.

---

## UTM Parameter Requirements

The link in the final post must include UTM parameters:
- `utm_source=twitter`
- `utm_medium=social`

Store in `format_metadata.utm_params` as `{"utm_source": "twitter", "utm_medium": "social"}`.

**CRITICAL — URL construction:**  Build the blog link from the `blog_url` field in `cli-kenwood content get <id>`, then append `?utm_source=twitter&utm_medium=social`.  **Do NOT use the Kenwood `slug` field** — it contains a date prefix and ID suffix (e.g. `2026-04-03-my-post-11`) that produce broken links.  The correct URL uses only the title slug (e.g. `https://otagelabs.com/blog/my-post`).

---

## Anti-Patterns

1. **Extracting the hook post from the LinkedIn version.**  The X thread hook must be native to X.  Different platform, different scroll behaviour, different audience expectations.
2. **Posts that exceed 280 characters.**  Each post must be independently within limit.  "Close enough" is not acceptable -- the API will reject it.
3. **Repeating the same idea across posts.**  Each post earns the next.  If post 3/ restates post 2/ with different words, cut it.
4. **Lecture-style threading.**  X threads that read like a classroom presentation die.  Each post should feel like a standalone observation that connects to the next.
5. **Begging for engagement.**  "RT if you agree" or "Drop a comment" signals desperation.  The content drives engagement.
6. **Thread padding.**  If the argument fits in 3 posts, do not stretch to 5.  Tighter is better on X.
7. **Links in every post.**  Only the final post gets the blog link.

---

## format_metadata Output Specification

Each X thread variant must include a `format_metadata` JSON object with these fields:

```json
{
  "thread_count": "<int, 3-5>",
  "is_thread": true,
  "per_post_char_counts": ["<int>", "...one per post"],
  "posts": [
    {"index": 1, "text": "1/ ..."},
    {"index": "<int>", "text": "<n>/ ..."}
  ],
  "featured_image_ref": "<string, storyboard image path or null>",
  "utm_params": {"utm_source": "twitter", "utm_medium": "social"}
}
```

---

## Example Output

Thread body (all posts concatenated for review):

```
1/ Most AI agents work in demo.  They fail in production.  Not because the model is wrong -- because nobody tested what happens at 3am on a Saturday.

2/ The gap between "works on my machine" and "works in production" is where every team underestimates.  Context windows overflow.  Retry logic loops.  Error handling catches the exceptions you imagined, not the ones that happen.

3/ The fix isn't more testing.  It's testing failure modes that only appear under production conditions -- rate limits, conversation history overflow, concurrent sessions.

4/ I've been debugging production agents for six months.  The pattern is consistent.  Full breakdown: https://otagelabs.com/blog/agent-debugging?utm_source=twitter&utm_medium=social
```

format_metadata.posts:

```json
[
  {"index": 1, "text": "1/ Most AI agents work in demo.  They fail in production.  Not because the model is wrong -- because nobody tested what happens at 3am on a Saturday."},
  {"index": 2, "text": "2/ The gap between \"works on my machine\" and \"works in production\" is where every team underestimates.  Context windows overflow.  Retry logic loops.  Error handling catches the exceptions you imagined, not the ones that happen."},
  {"index": 3, "text": "3/ The fix isn't more testing.  It's testing failure modes that only appear under production conditions -- rate limits, conversation history overflow, concurrent sessions."},
  {"index": 4, "text": "4/ I've been debugging production agents for six months.  The pattern is consistent.  Full breakdown: https://otagelabs.com/blog/agent-debugging?utm_source=twitter&utm_medium=social"}
]
```
