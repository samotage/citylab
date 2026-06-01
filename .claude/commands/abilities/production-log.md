---
description: "Log completed deliverables to the production log. Use after completing any artifact before ending the session."
---

# Production Log Discipline

## Procedure

After completing any deliverable, before ending the session, append one row to the Production Log in your experience file.

### Methodology

1. Locate your experience file at: `otl_support/claude_headspace/data/personas/<your-slug>/experience.md`
2. Append one row to the Production Log table in the format:
   `| YYYY-MM-DD | Artifact name | ≤18-word description | file path or "workshop" |`
3. Use today's date (from your time anchor), name the artifact clearly, keep the description under 18 words, and give the file path or "workshop" if it was a collaborative session.

### Rules

- An unlogged deliverable is an invisible deliverable.
- Production logs are the institutional record — without them, successors can't audit what was built or trace decisions back to their source.
- Log every deliverable: documents, specs, skill files, code changes, workshop outputs.
- One row per deliverable.  If a session produced three artifacts, that's three rows.
