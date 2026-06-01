# Blog Pipeline Skills

Two processes move a blog post from raw idea to live on the website with variants distributed across platforms.

## Process 1: Content Publishing (automatic after approval)

```
10-capture-idea  ->  20-ideate-post  ->  30-approve-content  ->  [35-storyboard]  ->  [ 40-export  ->  50-spiderweb  ->  60-publish-live ]
     Idea                Draft           Approved (last gate)      Optional visual       |<---------- automatic pipeline ---------->|
   (Kenwood)           (Kenwood)           (Kenwood)               (Kenwood)            (Website repo)         (Website repo)        (Website repo)
```

Steps 10-30 are operator-driven with human gates.  Step 35 (storyboard) is optional and operator-initiated; not every post needs visuals.  After content approval (step 30), steps 40-50-60 run as an automatic pipeline with zero operator gates.  The operator approves the content once, then watches flash banners confirm each stage: "Exported" → "SEO optimised" → "Published to otagelabs.com".

The pipeline halts on failure at any step.  The operator is notified via flash banner with the failure reason and the content piece's current state.  No automatic retry.

## Process 2: Variant Generation (operator-initiated, separate)

Variant generation and publishing is a separate process initiated by the operator after reviewing the live site.  There is no automatic handoff from Process 1 to Process 2.

The operator starts variant generation when ready (e.g., "generate variants for content piece #42" or by invoking `/kenwood-variant-generate` directly).  All existing variant gates (angle confirmation, variant review before posting) remain in place.

## Pipeline Detail

| Step | Skill | What it does | Autonomous? | Input | Output |
|------|-------|-------------|-------------|-------|--------|
| 10 | `/kenwood-blog-10-capture-idea` | Quick-capture a raw idea.  Pit stop, not a workshop. | No | Trigger message with the idea | Idea in Kenwood with seeded body |
| 20 | `/kenwood-blog-20-ideate-post` | 5-phase conversational workshop: absorb, angle, outline, iterate, draft. | No | Idea ID | ContentPiece in `draft` status |
| 30 | `/kenwood-blog-30-approve-content` | Generate editorial metadata (summary, meta description, tags) as a batch.  Transition to `approved`. | No (last gate) | Content piece ID | ContentPiece in `approved` status with metadata populated |
| 35 | `/kenwood-blog-35-generate-storyboard` | Create and generate visual storyboard images.  Optional; not every post needs visuals. | No (optional) | Content piece ID | Storyboard with generated images in `content/storyboards/` |
| 40 | `/kenwood-blog-40-otagelabs-export` | Export to the otageLabs website blog directory.  Transforms frontmatter, copies storyboard images. | **Yes** | Content piece ID | Markdown file + images in website repo |
| 50 | `/kenwood-blog-50-aso-spiderweb` | Apply cross-links and ASO fixes autonomously.  Flag destructive changes for operator approval. | **Yes** (non-destructive) | Post slug | Updated markdown files with inline links and `related_posts` frontmatter |
| 60 | `/kenwood-blog-60-publish-live` | Commit, PR to main, merge, verify Vercel deployment. | **Yes** | Auto-detected from git changes | Live blog post at otagelabs.com |

## Trust boundaries

- **`approved` status** is the trust boundary between operator oversight and autonomous execution.  The precondition gate on `draft → approved` guarantees summary, meta_description, and tags are populated.  After approval, the automatic pipeline runs without further operator gates.
- **Steps 10-30** are operator-driven — the operator participates in content creation and editorial review.
- **Step 40** copies from Kenwood to the website autonomously.
- **Steps 50-60** operate entirely on the website repo autonomously.  Step 60 commits, merges, and verifies deployment.
- **Process boundary:** Publishing (Process 1) ends when the content piece is live.  Variant generation (Process 2) begins when the operator explicitly initiates it.  There is no automatic connection between the two.

## Gaps between numbers

The numbering leaves room for future additions.  Step 35 (storyboard generation) was the first addition to the original 10/20/30/40/50/60 sequence.

## Skill file location

All skills live in `.claude/skills/` (symlinked from `otl_support/python/.claude/skills/`).  Each skill has a `SKILL.md` file; some have co-located reference files (e.g., `voice.md`, `post-formats.md` in the ideate skill).
