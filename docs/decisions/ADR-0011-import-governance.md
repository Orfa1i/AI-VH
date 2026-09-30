# ADR-0011: Import-Command Governance for Sign-off Status Changes

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Project Owner (plan update) & AI Agent (implementation)
- **Governing Documents**: updated `plan/CLAUDE.md`, STEP-02/05/18/25/53 prompts

---

## 1. Context

The owner tightened the sign-off rule: a status changes only through an import
command applying exactly what the sign-off lists. Two required commands did
not exist (`vh golden chunkmap-import`, `vh safety import-signoff`), and
STEP-53 needs a new `training.min_preference_pairs` threshold key.

## 2. Decision

- `vh golden chunkmap-import --signoff --chunkmap`: parses
  `CHUNGMAP-CORRECTION: <case> | <locator-substring> | <field> = <value>` lines
  (fields: status, matched_doc_id, reason); applies atomically; zero
  corrections is a byte-identical no-op; unmatched targets abort unwritten.
- `vh safety import-signoff --signoff --safety-dir` (suite `vh safety`):
  `Verdict: APPROVED` sections flip only the named tables to reviewed (+
  reviewer/date); `SAFETY-CORRECTION` lines update single row scalars.
  Edits are surgical line replacements so curated file comments survive
  (proven on a copy of the real `red_flags.yaml`).
- `TrainingThresholds.min_preference_pairs: Optional[int] = None`; the loader
  resolves schema-known but file-absent keys to their default (NOT SET, so
  STEP-53 stays BLOCKED) instead of raising, while truly unknown keys still
  raise. `REQUIRED_KEYS` is untouched until the owner adds the yaml key.
- Existing `vh golden import-signoff` behavior unchanged (STEP-05 suite green).

## 3. Consequences

- Owner actions outstanding: add `min_preference_pairs: null` under
  `training:` in `configs/thresholds.yaml` (then set a value before STEP 53),
  then I add the key to `REQUIRED_KEYS`. H6 still blocks Phase 6.
