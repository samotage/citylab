---
name: bidirectional-specification-audit
description: "Bidirectional spec-vs-code reconciliation audit. Finds unimplemented specs, unwired code, spec drift, redundant duplication, and accidental complexity — with sympathy for earned complexity."
category: Review
tags: [review, specification, compliance, complexity, audit]
---

# Bidirectional Specification Audit

**You are performing a reconciliation audit between specifications and implementation.** The running code is ground truth. Specifications are historical documents that may or may not have kept pace with reality.

**This is a read-only analysis with human-review findings.** Do not modify any code or specifications. Produce a structured report with findings that require human judgment.

**Philosophy:** Plans are redundant once battle is joined. PRDs describe intent. Specs describe expected behaviour. Code describes what actually happens. When these three diverge — and they always do — the audit's job is to surface the divergences, not to judge which is "right." That's the human's call.

---

## Step 0: Determine Audit Scope

### 0a. Identify Available Artifacts

Scan for available specification artifacts:

```bash
# OpenSpec specs
ls openspec/specs/ | sort

# PRD subsystems
find docs/prds -type d -maxdepth 2 | sort

# OpenSpec archived changes
ls openspec/changes/archive/ | sort
```

### 0b. Ask the User

Use `AskUserQuestion` with these questions:

**Question 1 — Subsystem scope:**
- **"Specific subsystem"** (Recommended) — let the user pick one or more subsystems (e.g., voice-bridge, hooks, persona). Best for thorough analysis within context window limits.
- **"Recent changes only"** — audit specs related to files changed in the last N days/commits. Good for checking recent work landed correctly.
- **"Full codebase"** — scan all specs against all code. WARNING: 60+ specs will push context limits. Best done subsystem-by-subsystem.

If the user picks "Specific subsystem", present the list of available OpenSpec spec directories and PRD subsystem directories. Allow multi-select.

If the user picks "Recent changes only", ask for a time window (same approach as the adversarial review's scope selection — bookmark tag, N days, specific commit, or branch diff).

**Question 2 — Audit focus (multi-select):**
Which reconciliation patterns should this audit prioritise?
- **"Unimplemented specs"** — specified in PRD/spec but missing from code. The lazy-agent detector.
- **"Unwired code"** — built but never called, registered but never used. The forgot-to-plug-it-in detector.
- **"Spec drift"** — code works differently than spec describes. Code is probably right; spec needs updating.
- **"Redundant duplication"** — same thing implemented twice without clear reason. The mindless-copy detector.
- **"Accidental complexity"** — over-engineering that isn't earning its keep. Sympathetic to earned complexity.
- **"All of the above"** (Recommended)

**Question 3 — Depth:**
- **"Requirements-level"** (Recommended) — cross-reference spec requirements and scenarios against code. Checks that each specified behaviour has a corresponding implementation.
- **"Task-level"** — also check OpenSpec change task lists (`tasks.md`) for completed tasks that may not have been fully wired in. More granular but uses more context.

---

## Step 1: Gather Specification Artifacts

Based on the user's scope selection, read ALL relevant specification artifacts.

### 1a. OpenSpec Specs

For each spec in scope, read `openspec/specs/{name}/spec.md`. Extract:
- Every **Requirement** heading
- Every **Scenario** (Given/When/Then)
- Key behavioural assertions (SHALL, MUST, etc.)

Build a **requirements inventory** — a flat list of discrete, testable requirements with their source location.

**You MUST read every spec file in the target scope. After building the inventory, verify completeness by listing the spec files read and confirming none were skipped.**

### 1b. PRDs

For each PRD subsystem in scope, read the PRD files in `docs/prds/{subsystem}/done/`. Extract:
- **Success criteria** (functional and non-functional)
- **In-scope items** from the Scope section
- **Key requirements** from the Requirements section

Add these to the requirements inventory, noting which PRD they came from.

### 1c. OpenSpec Changes (if task-level depth selected)

For each relevant archived change in `openspec/changes/archive/`, read:
- `tasks.md` — the implementation task list
- `proposal.md` — what was proposed to change
- `compliance-report.md` — what was verified at archive time

Note any tasks marked complete that relate to the specs in scope.

### 1d. Architecture Docs

Check `docs/` for any architecture documents relevant to the subsystems in scope. These provide context for design decisions that may explain apparent divergences.

---

## Step 2: Map Implementation Against Specifications

For each requirement in the inventory, trace it to the codebase.

### 2a. Locate Implementation

For each requirement/scenario:
1. Identify the expected implementation location (service, route, model, template, JS module)
2. Search the codebase for the implementation — use service names, function names, route paths, model fields mentioned in the spec
3. Read the actual implementation code
4. Assess: **Implemented / Partially Implemented / Not Implemented / Implemented Differently**

### 2b. Check Wiring

For code that exists, verify it's actually reachable:
- Is the service registered in `app.extensions`?
- Is the route blueprint registered in `app.py`?
- Is the function called from anywhere?
- Is the JS module imported/loaded?
- Is the template rendered by any route?
- Are model fields used by any query or assignment?

**The "built but never wired" pattern is specifically what we're looking for here.** Agents commonly build a service, write tests for it in isolation, and never connect it to the actual application flow.

### 2c. Reverse Scan — Code Without Specs

For the subsystems in scope, scan the implementation code for functionality that has NO corresponding spec:
- Services with public methods not described in any spec
- Route endpoints not mentioned in any PRD or spec
- Model fields not specified anywhere
- JS features or UI elements not in any PRD

This isn't automatically a problem — emergent functionality from real usage is expected. But it should be documented.

---

## Step 3: Complexity Assessment

**Critical principle: Complexity is only a problem when it's not earning its keep.**

For each subsystem in scope, assess complexity with sympathy for the problem domain.

### 3a. Earned Complexity Indicators

The following signal that complexity is justified — do NOT flag these as problems:
- **Multiple edge cases from real bugs** — if git history shows iterative fixes adding branches, the branches are battle scars, not gold-plating
- **Protocol complexity** — WebRTC, SSE reconnection, tmux escape sequences, AppleScript bridging all have inherent complexity
- **State machine transitions** — systems that genuinely need multi-state management (command lifecycle, agent states)
- **Cross-system coordination** — voice bridge talking to tmux talking to SSE talking to the dashboard is complex because the problem is complex
- **Error recovery paths** — retry logic, graceful degradation, fallback chains that exist because things actually fail in production

### 3b. Accidental Complexity Indicators

Flag these:
- **Abstraction for one caller** — a service class with one public method called from one place. Could be a function or inlined.
- **Configuration indirection** — config-driven strategy selection where only one strategy exists
- **Defensive code for impossible states** — None-checks after guaranteed-present lookups, try/except for code that can't raise
- **Premature generalization** — plugin systems, registries, factory patterns serving a single implementation
- **Copy-paste with minor variation** — same logic repeated with small tweaks instead of parameterized

### 3c. Redundant Duplication Assessment

For each potential duplication found:
- **Is it intentional isolation?** — Sometimes two services deliberately don't share code to prevent coupling. That's a feature, not a bug.
- **Is it legacy?** — Old approach still present alongside its replacement. One should be removed.
- **Is it mindless?** — Agent copied a pattern without understanding why. Technical debt.

### 3d. Dead Code Detection

Scan for:
- Imported but unused modules
- Defined but uncalled functions/methods
- Registered but unreferenced routes
- Model fields that are written but never read (or vice versa)
- CSS classes defined but never used in templates
- JS functions defined but never called

---

## Step 4: Produce the Report

Create the report directory if it doesn't exist:
```bash
mkdir -p docs/reviews_remediation/specification
```

Write the report to `docs/reviews_remediation/specification/YYYY-MM-DD.md` using today's date.

If a file with that date already exists, append a suffix: `YYYY-MM-DD-2.md`.

### Report Template

```markdown
# Bidirectional Specification Audit — YYYY-MM-DD

## Audit Parameters
- **Subsystems audited:** [list]
- **Artifacts scanned:** N specs, N PRDs, N change records
- **Focus areas:** [list of selected patterns]
- **Depth:** requirements-level / task-level

## Executive Summary

[2-3 paragraphs: overall alignment assessment between specs and code. What's the general health? Are specs keeping up with implementation? Is implementation keeping up with specs? Where are the biggest gaps? What's the "specification debt" — how much documentation work is needed to bring specs in line with reality?]

---

## Findings by Category

### Unimplemented Specifications

Requirements that exist in specs/PRDs but have no corresponding implementation.

| # | Source | Requirement | Expected Location | Severity | Notes |
|---|--------|-------------|-------------------|----------|-------|
| 1 | spec: voice-bridge | "SHALL support..." | services/voice_*.py | HIGH — core feature missing | Likely deferred, not forgotten |

**Assessment:** [Are these genuine misses, conscious deferrals, or requirements that turned out to be unnecessary? Recommend which ones actually need implementing vs. which specs should be updated to remove them.]

### Unwired Code

Code that exists but is not reachable from any entry point.

| # | Location | What It Does | Spec Reference | Likely Cause |
|---|----------|-------------|----------------|--------------|
| 1 | services/foo.py:42 | FooService.bar() | spec: foo | Built, tested in isolation, never registered |

**Assessment:** [For each item — should it be wired in (the agent forgot), or should it be removed (it was superseded)?]

### Specification Drift

Where code behaviour differs from what the spec describes, and the code is known-working.

| # | Spec Says | Code Does | Location | Verdict |
|---|-----------|----------|----------|---------|
| 1 | "Returns 404 on missing" | Returns 204 with empty body | routes/foo.py:23 | Code is correct — spec needs updating |

**Assessment:** [For each — does the spec need updating, does the code need fixing, or is this a conscious trade-off that should be documented?]

### Redundant Duplication

Same logic implemented in multiple places without clear justification.

| # | Location A | Location B | What's Duplicated | Type |
|---|-----------|-----------|-------------------|------|
| 1 | services/a.py:10 | services/b.py:45 | Session validation | Mindless copy |

**Assessment:** [For each — is this intentional isolation (keep both), legacy (remove one), or mindless duplication (refactor)?]

### Accidental Complexity

Over-engineering that isn't justified by the problem domain.

| # | Location | Pattern | Problem | Simpler Alternative |
|---|----------|---------|---------|-------------------|
| 1 | services/foo.py | Registry with 1 impl | Indirection without payoff | Inline or direct function call |

**Assessment:** [For each — what's the simplification, what's the risk, is it worth doing now?]

### Dead Code

Code that exists but is never reached.

| # | Location | Type | Description |
|---|----------|------|-------------|
| 1 | services/foo.py:42 | Unused function | `_legacy_handler()` — no callers |

---

## Earned Complexity — Leave Alone

Modules or patterns that look complex but earn their complexity. Documented here so future audits don't re-flag them.

| Subsystem | Complexity Level | Why It's Justified |
|-----------|-----------------|-------------------|
| voice-bridge | High | WebRTC + semantic matching + multi-format responses — problem domain is inherently complex |

---

## Specification Health Scorecard

| Subsystem | Spec Coverage | Code-Spec Alignment | Spec Freshness | Action Needed |
|-----------|--------------|--------------------|-----------------|-|
| hooks | 90% | Good — minor drift | Current | Update 2 scenarios |
| voice-bridge | 60% | Significant drift | Stale | Major spec revision needed |

**Coverage:** % of implemented features that have corresponding spec entries
**Alignment:** How well the spec describes what the code actually does
**Freshness:** Whether the spec reflects the current state or a historical state

---

## Recommended Actions

Prioritised list of actions. Each item tagged with who needs to act.

### Spec Updates Needed (documentation work)
1. **[SPEC]** Update voice-bridge spec to reflect current implementation — spec describes v1, code is v3
2. ...

### Implementation Gaps (code work)
1. **[CODE]** Wire up FooService — built and tested but never registered
2. ...

### Cleanup Opportunities (optional improvement)
1. **[CLEANUP]** Remove legacy `_old_handler` from bar.py — superseded by new flow
2. ...

### Complexity Reduction (optional simplification)
1. **[SIMPLIFY]** Inline BazRegistry — only one implementation, indirection adds no value
2. ...

---

## Files Reviewed
<list of all spec/PRD files scanned and code files inspected>
```

---

## Step 5: Present Summary to User

After writing the report, present a concise summary:

- **Alignment score** — rough percentage of specs that match implementation
- **Top findings** — the 3-5 most important items across all categories
- **Spec debt estimate** — how many specs need updating to reflect reality
- **Implementation gaps** — genuine missing features (not spec drift)
- **Quick wins** — things that can be fixed immediately (dead code removal, unwired services)
- **Report location**

Ask the user which findings they want to discuss or act on.

**Do NOT auto-commit, auto-fix, or auto-update any files.** This audit produces findings for human review. The user decides what to act on.

---

## Context Window Management

**CRITICAL:** Scanning specs AND code for even a single subsystem consumes significant context.

1. **Process one subsystem at a time** — read its specs, check its code, record findings, then release the file contents before moving to the next subsystem.
2. **Build findings incrementally** — don't hold all spec content in memory while scanning code. Extract requirements into a compact list, release the spec text, then check code against the list.
3. **Spec summaries, not full text** — when recording findings, reference spec locations (`spec: voice-bridge, Requirement: Audio Streaming, Scenario: Reconnection`) rather than quoting full Given/When/Then blocks.
4. **Write the report section-by-section** — don't accumulate everything in memory and write at the end. Write each category's findings as you complete it.
5. **If context pressure builds** — prioritise completing the current subsystem thoroughly over starting another one. A deep audit of 3 subsystems beats a shallow scan of 10.
