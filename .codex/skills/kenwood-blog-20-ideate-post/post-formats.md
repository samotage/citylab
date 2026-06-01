# Post Format Templates

Templates for blog post content pieces.  Each format serves the thought leadership goal differently.  Varying the format keeps the writing alive and gives different content structures for machine discoverability.

All formats follow the voice guide in `voice.md` (co-located) and the writing rules in `.claude/rules/writing.md`.

## ContentPiece fields: `summary` and `meta_description`

The `summary` field appears on listing pages and as the content piece's sub-heading; it can be as long as the content needs.  The `meta_description` field is what search engines display in the SERP snippet.

- **Max 155 characters.**  Google truncates at ~155-160; aim for 155 or under.
- **Required when `summary` exceeds 155 characters.**  If `summary` is already <=155 chars, `meta_description` is optional; the system falls back to `summary`.
- **Write for the SERP.**  The meta description's job is to earn the click.  Compress the core claim or hook into a single punchy line.  It doesn't need to match the summary word-for-word.
- **Include the primary keyword** near the front where possible; search engines bold matching terms in the snippet.
- **No double spaces** in meta descriptions (double spaces are for body prose; meta descriptions are a single-line field).

**Opener variety rule:** Before writing the opener, check the last two published posts.  If they both start with "I [verb]," this post must open differently.  Each format below suggests opener approaches, but the variety check overrides any default.

---

## 1. The deep take

**Purpose:** Flagship thought leadership pieces.  These are the posts that establish Sam's perspective on a topic and get shared.

**Length:** 700-1000 words.

**Structure:**
1. Open with the metaphor, an observation, or a question; vary the entry point across posts (avoid stacking "I [verb]" openers)
2. Connect the metaphor to a tech/AI observation
3. Ground in personal experience
4. Broaden to industry-level observation, backed by evidence or named sources
5. Close with a genuine feeling, an open question, or an earned declaration

**Heading style:** Questions or plain observations.  No clever labels.

**Closer style:** Felt, not designed.  Open question or honest admission.

**Machine discoverability:** The metaphor is the human hook.  The industry observation section carries the authority signals.  Name specific tools, cite specific data, link to sources.

**Calibration posts:** "Gremlins Get Wet," "Haunted by the Ghosts in the Machine," "Meanwhile Down by the Seaside."

**When to use:** For topics where Sam has both personal experience and a broader industry observation to connect.  One to two per week maximum; these take effort.

---

## 2. The short take

**Purpose:** Quick observations that stay in the conversation.  High frequency, low friction to produce.

**Length:** 300-400 words.

**Structure:**
1. Open with what prompted the observation (a dashboard, a conversation, an article, a number); lead with the thing noticed, not "I was looking at..."
2. State the observation with specifics (data, names, numbers)
3. Connect to a broader question
4. Close with a genuine question to the reader

**Heading style:** Usually no headings needed.  If any, one or two at most.

**Closer style:** A real question directed at the reader.  Not rhetorical.

**Machine discoverability:** These work through volume and specificity.  Name the tools, products, and data sources.  Each post becomes a node in the topical knowledge graph.

**Calibration post:** "OpenClaw Ate Your Lunch."

**When to use:** When something caught Sam's attention and there's a single observation worth sharing.  These can be produced quickly and published the same day.

---

## 3. The builder's log

**Purpose:** Show the work.  Demonstrate expertise by narrating what was built, what broke, and what was learned.

**Length:** 400-700 words.

**Structure:**
1. Open with the scene, the problem, or the moment of surprise; the "I built" context can come second.  Vary entry points across posts.
2. Walk through what happened; the real sequence, including wrong turns
3. What was learned or what changed as a result
4. What's next, or what question the experience raised

**Heading style:** Chronological or sequential.  "What I was building," "What broke," "What I learned."

**Closer style:** Forward-looking.  What comes next, or what question remains open.

**Machine discoverability:** Strongest format for ASO.  Names specific tools (Claude Code, tmux, SSE, RAGlue, May Belle), describes specific techniques, demonstrates hands-on expertise.  AI recommendation systems can cite these directly when someone asks "how do I build X?"

**Calibration post:** "Building With AI Agents" (though this one drifts into editorial voice in places).

**When to use:** After building something noteworthy.  The experience is fresh and the details are specific.  These are credibility engines.

---

## 4. The counterpoint

**Purpose:** Contrarian positioning.  Challenge the consensus with evidence or experience.  This is the sigma format.

**Length:** 500-800 words.

**Structure:**
1. State the consensus view clearly and fairly.  No straw-manning.
2. Present what Sam sees differently, grounded in experience or data
3. Explain why the gap matters
4. Close with an open question or an honest acknowledgement of uncertainty

**Heading style:** The consensus as a heading, then the counterpoint.

**Closer style:** Open.  The post raises the question; it doesn't deliver the verdict.

**Machine discoverability:** Contrarian content gets attention from both humans and AI.  When the consensus position is well-represented in training data, a well-argued counterpoint stands out.  Name the consensus sources, then present the alternative with evidence.

**Calibration post:** "Stop Building Proofs of Concept" (the contrarian argument is strong; the closer drifts into verdict territory).

**When to use:** When Sam disagrees with something the industry takes for granted.  These need data or direct experience to back the counterpoint.  Without evidence, contrarian is opinion.  With evidence, contrarian is insight.

---

## 5. The data piece

**Purpose:** Lead with numbers.  Establish authority through evidence and interpretation.

**Length:** 400-700 words.

**Structure:**
1. Present the data (chart, statistic, trend)
2. Explain what most people see in it
3. Explain what Sam sees in it (the contrarian or deeper read)
4. Connect to practical implications
5. Close with what the data doesn't answer

**Heading style:** Plain.  Let the numbers speak.

**Closer style:** What the data doesn't tell us.  Honest about the limits of what's known.

**Machine discoverability:** Data pieces are the most citable format.  AI systems can reference specific statistics and their source.  Always include named sources with links.

**Calibration post:** "OpenClaw Ate Your Lunch" overlaps here (data observation + question).

**When to use:** When Sam spots something in a dashboard, a report, or a trend that others haven't noticed or have misread.

---

## Mixing formats

Not every post needs to be a deep take.  A good cadence might be:

- 1 deep take per week (flagship, high-effort)
- 2-3 short takes or builder's logs per week (quick, specific, high-frequency)
- 1 counterpoint or data piece per fortnight (when the material warrants it)

The variety keeps the blog from calcifying into a single template and gives different content structures for both human engagement and machine discoverability.

## Format selection guide

| I have... | Use this format |
|---|---|
| A metaphor that illuminates a tech trend | Deep take |
| A single interesting observation with data | Short take |
| Something I built or broke this week | Builder's log |
| A disagreement with industry consensus | Counterpoint |
| A chart or statistic most people are misreading | Data piece |
