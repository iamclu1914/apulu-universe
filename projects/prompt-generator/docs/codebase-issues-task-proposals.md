# Codebase Issue Review — Task Proposals

## 1) Typo Fix Task
**Title:** Fix typo in Seedance compliance comment in `agents/pipeline.js`

- **Issue found:** A comment in the Seedance compliance section contains an accidental fragment: `...also wiki/vawn-mix-engine/... no` which reads like an unfinished edit.
- **Why it matters:** This lowers maintainability and makes canonical-rule provenance unclear.
- **Proposed task:** Rewrite the comment into a single clear sentence pointing to the canonical in-repo source and (optionally) one external reference path.
- **Acceptance criteria:** No stray fragment remains; comment is grammatically correct and unambiguous.

## 2) Bug Fix Task
**Title:** Fix stale mode names in `tests/pipeline.test.js` that now crash/throw

- **Issue found:** Tests call removed modes (`mv`, `kling-9grid`, `kling-startend`) even though `MODE_CONFIG` now uses `hf-*` mode names and removed Kling support.
- **Observed failure:** `npm test` fails in `tests/pipeline.test.js` and also references a removed module (`../agents/video-director`).
- **Why it matters:** CI is red and test results no longer validate current behavior.
- **Proposed task:** Update tests to align with current modes (`hf-mv`, `hf-9grid`, `hf-startend`, etc.), and remove/replace imports that reference deleted modules.
- **Acceptance criteria:** `npm test` passes without module-resolution errors; mode assertions reflect current `MODE_CONFIG`.

## 3) Comment/Documentation Discrepancy Task
**Title:** Reconcile outdated comments and docs that mention removed Kling pipeline

- **Issue found:** Multiple comments/docs still mention Kling-era behavior while code has moved to Higgsfield/Seedance-only routing.
- **Why it matters:** Mismatch between comments and runtime behavior increases onboarding and maintenance errors.
- **Proposed task:** Sweep `tests/`, `docs/`, and key pipeline comments to remove Kling-era instructions where no longer applicable, or clearly mark them as historical context.
- **Acceptance criteria:** Core docs and test comments reflect current product behavior and naming.

## 4) Test Improvement Task
**Title:** Add regression tests for guardrail sanitization in `applyPromptGuardrails`

- **Issue found:** Guardrail logic is complex (negative-term trimming, max-char truncation, `Negative:` stripping, format warnings), but no focused unit tests cover all branches.
- **Why it matters:** Regressions in sanitization can silently degrade prompt quality and generation reliability.
- **Proposed task:** Add table-driven tests for:
  - trimming negatives to `MAX_NEGATIVE_TERMS`
  - truncating prompts to `MAX_PROMPT_CHARS`
  - stripping `Negative:` for Higgsfield flows
  - warning on banned trigger words/reflection mechanics/long focal lengths
- **Acceptance criteria:** New tests fail on intentional regressions and pass on current expected behavior.
