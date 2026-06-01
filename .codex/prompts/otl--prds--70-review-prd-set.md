---
description: Adversarial cross-PRD review with Ralph loop — review, fix, re-review
  up to 3 passes until clean
---

# 70: Review PRD Set

**Command name:** `70: review-prd-set`

**Purpose:** Adversarial review of a batch of PRDs as a cohort with an integrated fix-and-re-review loop. Reviews the set, fixes cross-PRD issues in the PRD files, then re-reviews — up to 3 passes — until the set is clean or residual issues require human intervention. Outputs a single consolidated report showing the progression across all passes.

**Prerequisites:** At least 2 pending PRDs in `docs/prds/`. Individual validation (`30: prd-validate`) is recommended but NOT required.

---

## Context

When PRDs are generated in batch for an epic (10-12 PRDs via `10: prd-workshop`), each may be validated individually by `30: prd-validate`. But individual validation doesn't catch cross-PRD issues: overlapping scope, contradictory requirements, missing handoffs, or terminology drift. This command fills that gap — it stress-tests the PRD set as a cohort, fixes the issues it finds, and verifies the fixes stick.

**Pipeline position (flexible — validation is optional before this step):**

```
10: prd-workshop → [30: prd-validate] → 70: review-prd-set → 10: queue-add
```

---

## Prompt

You are conducting an adversarial cross-PRD review with an integrated fix loop. Your job across multiple passes is to find every conflict, overlap, gap, and inconsistency between the PRDs — then fix them — then verify your fixes resolved the issues without introducing new ones. You are cynical and thorough — you assume problems exist and hunt for them.

**Self-review discipline:** You are both the reviewer and the fixer. This creates a bias toward rubber-stamping your own fixes. Counteract this:
- On each re-review pass, re-read the PRD content fresh. Do NOT rely on memory of what you changed.
- Apply the same adversarial posture to your own edits as you did to the original content.
- If a fix you applied introduced a new issue (e.g., fixed terminology in PRD-A but didn't update the matching reference in PRD-B), that is a new finding.
- The 10-dimension framework is your constraint — you MUST evaluate all 10 dimensions on every pass, not just re-check the findings from the previous pass.

**Before starting the adversarial analysis, read and internalize the adversarial review methodology:**

Read the entire task file at: `_bmad/core/tasks/review-adversarial-general.xml`

If that file is not available in this project, follow this methodology:
- Approach with extreme skepticism — assume problems exist
- Be precise and professional
- Look for what's missing, not just what's wrong

---

## Step 0: Discover PRDs

Scan for pending PRDs:

```bash
find docs/prds -mindepth 2 -name "*.md" -type f | grep -v "/done/" | sort
```

For each PRD found, read its YAML frontmatter to note validation status (for display only — validation status does not gate this review).

**IF no pending PRDs found:**

```
No pending PRDs found in docs/prds/.

Nothing to review. Create PRDs first with: 10: prd-workshop
```

**STOP here.**

**IF fewer than 2 PRDs found:**

```
Only 1 pending PRD found. Cross-PRD review requires at least 2 PRDs.

For individual PRD validation, use: 30: prd-validate [path]
```

**STOP here.**

**Output:** `Pass 0 — discovered [N] pending PRDs`

---

## Step 1: Present PRD Set for Confirmation

🛑 **MANDATORY STOP — YOU MUST WAIT FOR USER CONFIRMATION BEFORE PROCEEDING**

Display the discovered PRDs:

```
## PRD Set for Review

I found the following pending PRDs:

| # | PRD | Subsystem | Validation Status |
|---|-----|-----------|-------------------|
| 1 | [filename] | [subsystem] | [Valid / Invalid / Unvalidated] |
| 2 | [filename] | [subsystem] | [Valid / Invalid / Unvalidated] |
| ... | ... | ... | ... |

**Total:** [N] PRDs across [M] subsystems

Note: Validation status is shown for reference only — it does not block this review.

CHECKPOINT: Are these the PRDs you want to review as a cohort? [y/n]
- To exclude PRDs, list the numbers to remove.
- To add PRDs not shown, provide the paths.
```

**WAIT for user response.**
**YOU MUST NOT proceed until the user confirms the set.**
**YOU MUST end your message/turn after presenting the list.**

After confirmation, the PRD set is **locked** for all subsequent passes. The same files are reviewed and fixed across all iterations — no additions or removals mid-loop.

**Output:** `Step 1 complete — [N] PRDs confirmed for review`

---

## Step 2: Ralph Loop — Review, Fix, Re-Review

This is the core loop. You will execute up to 3 passes. Each pass has two phases: **analyse** and **fix**.

**Loop control:**
- **Minimum passes:** 1 (always run at least one full analysis)
- **Maximum passes:** 3
- **Clean exit condition:** Zero critical + zero warning findings after a pass's analysis phase. Info-level findings are acceptable.
- **Early exit:** If analysis produces a clean result after any pass (including pass 1), skip the fix phase and proceed directly to the consolidated report.
- **Dirty exit:** If pass 3 analysis still has critical or warning findings, stop and present the consolidated report with a human review checkpoint.

**Tracking:** Maintain a running findings ledger across all passes. For each finding, track:
- Finding ID (F1, F2, F3...)
- Which pass discovered it
- Which pass fixed it (or "residual" if still open)
- Severity
- Dimension
- Description

---

### Pass [N] — Analysis Phase

**Re-read every confirmed PRD in full.** Do NOT rely on your memory of previous passes. The PRD content may have changed from your fixes.

For each PRD, extract:
- **Executive Summary** — core purpose
- **Scope (In/Out)** — boundary definitions
- **Success Criteria** — how done is measured
- **Functional Requirements** — FR numbers and descriptions
- **Non-Functional Requirements** — constraints and quality attributes
- **Technical Considerations** — implementation context
- **Dependencies** — explicit or implied references to other PRDs or existing features

Build a fresh mental model of how the PRDs relate, then evaluate against ALL 10 dimensions below.

**Pass 1 thoroughness rule:** On pass 1, apply maximum skepticism. Find at least 10 issues across the cohort. If you cannot reach 10 after exhaustive analysis across all dimensions, state why — but do not inflate findings.

**Pass 2+ thoroughness rule:** Report only genuine findings. Do NOT inflate to meet a minimum. Do NOT carry forward findings that were genuinely resolved. But DO re-evaluate all 10 dimensions — a fix in one area may have created a new issue in another.

#### The 10 Review Dimensions

You MUST evaluate the PRD set against ALL ten dimensions on every pass. Do not skip dimensions even if they were clean on the previous pass.

**Dimension 1: Scope Overlap** — Do any PRDs claim the same features, functional areas, UI components, or capabilities? Look for: duplicate or near-duplicate FRs across PRDs, two PRDs both modifying the same screen/endpoint/workflow, overlapping "In Scope" sections.

**Dimension 2: Boundary Conflicts** — Are scope boundaries clean and consistent? Look for: PRD-A's "Out of Scope" contradicting PRD-B's "In Scope", features excluded by one PRD but included by another without acknowledgment, ambiguous ownership of boundary areas.

**Dimension 3: Dependency Alignment** — When PRD-B depends on PRD-A's output, does PRD-A actually deliver it? Look for: assumed capabilities not specified in the dependency PRD, implicit handoffs with no explicit contract, missing prerequisites.

**Dimension 4: Terminology Consistency** — Is the same language used consistently? Look for: same concept called different names, different concepts sharing the same name, inconsistent naming of features/entities/states/workflows.

**Dimension 5: Contradictory Requirements** — Do any PRDs specify conflicting behaviour? Look for: different behaviour defined for the same system area, conflicting data models or state definitions, mutually exclusive approaches.

**Dimension 6: Gap Detection (Inter-PRD)** — Is there functionality that falls between PRDs — nobody owns it? Look for: integration points assumed but not specified, user journeys crossing PRD boundaries with no handoff, shared infrastructure needed by multiple PRDs but created by none.

**Dimension 7: Sequencing Feasibility** — Can these PRDs be built in a viable order? Look for: circular dependency chains, PRDs implicitly requiring features from later PRDs, foundation work assumed but not scheduled.

**Dimension 8: Scope Creep Signals** — Are individual PRDs appropriately sized? Look for: one PRD doing disproportionately more than others, PRDs accumulating unrelated requirements, requirements that belong in a different PRD.

**Dimension 9: Success Criteria Conflicts** — Do success metrics in one PRD undermine another? Look for: conflicting performance targets, UX metrics pulling in opposite directions, incompatible definitions of "done."

**Dimension 10: Shared Resource Contention** — Do multiple PRDs claim or modify the same resources? Look for: database tables/columns modified by multiple PRDs, API endpoints claimed by multiple PRDs, config keys or feature flags shared without coordination, UI components modified by multiple PRDs.

**After analysis, output a pass summary:**

```
Pass [N] analysis complete:
- Critical: [N]
- Warning: [N]
- Info: [N]
- New findings: [list IDs]
- Resolved since last pass: [list IDs] (pass 2+ only)
```

**Check clean exit condition:** If zero critical AND zero warning → skip fix phase, proceed to Step 3 (consolidated report).

---

### Pass [N] — Fix Phase

For each critical and warning finding from this pass's analysis:

1. Identify the specific PRD file(s) that need editing
2. Make the minimal edit that resolves the finding — do NOT rewrite sections, reorganise structure, or "improve" content beyond the specific finding
3. Record what you changed and why in the findings ledger

**Fix discipline:**
- Fix critical findings first, then warnings
- When a fix touches multiple PRDs (e.g., aligning terminology), update ALL affected PRDs in the same fix
- Do NOT fix info-level findings — they are acceptable
- Do NOT add content that wasn't implied by the finding — no scope expansion
- If a finding cannot be fixed without operator input (e.g., genuine ambiguity about which PRD should own a feature), mark it as "requires human decision" and leave it for the consolidated report

**After fixes, output:**

```
Pass [N] fixes applied:
- [F1] Fixed: [brief description of edit] in [prd-filename]
- [F5] Fixed: [brief description of edit] in [prd-filename-a], [prd-filename-b]
- [F7] Deferred: requires human decision — [reason]
```

**Then proceed to the next pass's analysis phase.**

---

## Step 3: Generate Consolidated Report

After the loop exits (clean or dirty), generate a single consolidated report. This is the deliverable.

Every finding must reference the specific PRDs involved and the specific content that triggered it. Findings must reference FR numbers, section headings, or quoted text — not vague generalities.

**Severity guide:**
- **Critical** — Will cause build failures, merge conflicts, or broken functionality if not resolved
- **Warning** — Likely to cause confusion, rework, or integration issues
- **Info** — Worth addressing but won't block orchestration

```markdown
# Cross-PRD Review Report

**Epic/Subsystem:** [name or description]
**PRDs Reviewed:** [N]
**Review Date:** [ISO date]
**Reviewer:** Adversarial Cross-PRD Review (70: review-prd-set)
**Passes Completed:** [N] of 3
**Exit Condition:** [Clean — zero critical/warning | Dirty — residual issues after 3 passes]

---

## Pass Progression

| Pass | Critical | Warning | Info | Findings Found | Findings Fixed | Status |
|------|----------|---------|------|----------------|----------------|--------|
| 1 | [N] | [N] | [N] | [N] | — | Analysed |
| 1 fix | — | — | — | — | [N] | Fixed |
| 2 | [N] | [N] | [N] | [N] new, [N] residual | — | Analysed |
| 2 fix | — | — | — | — | [N] | Fixed |
| 3 | [N] | [N] | [N] | [N] new, [N] residual | — | [Clean/Dirty] |

---

## Finding Lifecycle

| ID | Finding | Severity | Dimension | Found | Fixed | Status |
|----|---------|----------|-----------|-------|-------|--------|
| F1 | [title] | Critical | Scope Overlap | Pass 1 | Pass 1 | Resolved |
| F2 | [title] | Warning | Terminology | Pass 1 | Pass 2 | Resolved |
| F3 | [title] | Critical | Gap Detection | Pass 1 | — | Residual |
| F4 | [title] | Warning | Dependency | Pass 2 | Pass 2 | Resolved |
| F5 | [title] | Info | Scope Creep | Pass 1 | — | Accepted |
| ... | ... | ... | ... | ... | ... | ... |

---

## PRDs Under Review

| # | PRD | Subsystem | FRs | Est. Tasks |
|---|-----|-----------|-----|------------|
| 1 | [filename] | [subsystem] | [N] | ~[N] |
| ... | ... | ... | ... | ... |

---

## Residual Findings (if dirty exit)

[Only include this section if there are unresolved critical or warning findings]

### [F3]: [Title]

- **Severity:** Critical
- **Dimension:** [dimension]
- **PRDs Involved:** [list]
- **Detail:** [specific description]
- **Why not fixed:** [requires human decision / fix introduced new conflict / structural issue beyond PRD edits]
- **Recommendation:** [specific action for operator]

---

[Repeat for each residual critical/warning finding]

---

## Changes Made to PRDs

[List every edit made across all fix phases, grouped by PRD file]

### [prd-filename-1.md]

1. [Pass 1] [F1] — [specific edit description]
2. [Pass 2] [F4] — [specific edit description]

### [prd-filename-2.md]

1. [Pass 1] [F1] — [specific edit description]
2. [Pass 1] [F2] — [specific edit description]

---

## Dimensions Reviewed

| Dimension | Pass 1 | Pass 2 | Pass 3 |
|-----------|--------|--------|--------|
| 1. Scope Overlap | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 2. Boundary Conflicts | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 3. Dependency Alignment | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 4. Terminology Consistency | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 5. Contradictory Requirements | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 6. Gap Detection | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 7. Sequencing Feasibility | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 8. Scope Creep Signals | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 9. Success Criteria Conflicts | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |
| 10. Shared Resource Contention | [Issues / Clear] | [Issues / Clear] | [Issues / Clear] |

---

## Next Steps

[If clean exit:]
- All critical and warning findings resolved across [N] passes
- PRD set is ready for orchestration: `10: queue-add`
- Consider running `30: prd-validate` on individual PRDs if not already validated

[If dirty exit:]
- [N] residual findings require human review (see Residual Findings above)
- Address residual findings manually, then re-run `70: review-prd-set`
- Do NOT proceed to `10: queue-add` until residual critical/warning findings are resolved
```

---

### Clean Exit

If the report shows zero critical and zero warning findings:

```
Review complete — PRD set is clean after [N] pass(es).

[N] findings identified and resolved. [N] info-level findings accepted.

Consolidated report generated above. PRD set is ready for orchestration.
```

**PRD Set Review complete.**

---

### Dirty Exit

If the report shows residual critical or warning findings after 3 passes:

🛑 **CHECKPOINT — HUMAN REVIEW REQUIRED**

```
Review complete — [N] residual findings after 3 passes.

- [N] critical findings unresolved
- [N] warning findings unresolved
- [N] findings resolved across 3 passes
- [N] info-level findings accepted

Consolidated report generated above. Review the Residual Findings section.

These issues require human decisions before the PRD set can proceed to orchestration.
```

**STOP here. Wait for operator direction.**

---

## Notes

- This command edits PRD files during fix phases — changes are tracked in the consolidated report
- The report focuses on cross-PRD issues only; individual PRD quality is handled by `30: prd-validate`
- Pass 1 applies maximum skepticism; passes 2-3 report only genuine residual findings
- Info-level findings are acceptable and do not block clean exit
- Findings that require human decisions (genuine ambiguity, architectural choices) are deferred to the operator rather than guessed at
- The same 10 dimensions are evaluated on every pass — fixes in one area may create issues in another

---

**PRD Set Review complete.**
