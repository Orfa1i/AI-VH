# ADR-0013: Automated-Reviewed Case Track (Doctor-Free Training Accumulation)

- **Status**: Accepted (design approved by owner with independence mandate)
- **Date**: 2026-09-30
- **Deciders**: Project Owner (design + mandate) & AI Agent (implementation)
- **Governing Constraints**: no fabricated human reviews; human path untouched;
  no "doctor-final"/physician language on automated outputs; fail closed;
  no training started.

---

## 1. Predicate (all must hold; first failure short-circuits to reject)

1. Sanitized report (self-assessment fields stripped, paths logged).
2. `ClinicalReport` schema + referential integrity vs evidence ids.
3. Router `verify()` → `verified`, with `critical_count == 0` and zero
   unsupported/invalid citations asserted separately.
4. Scorer `dx_top1 == 1.0` and `red_flags_addressed == 1.0`.
5. Composite ≥ `t_approve` (0.50 proposed in `configs/training/curation.yaml`).
6. Correct-track only for single-class unsupported-claim defects: deletion-only
   repair (drop claims, prune dangling refs, insert abstentions; never add
   clinical content) followed by FULL revalidation (schema + router + scorer).
7. Gray zone, ambiguity, and every validator exception → reject with reason codes.

## 2. Independence enforcement

- Evaluator signature accepts DATA ONLY (`EncounterState`, `CaseSpec`,
  evidence dict) — no adapters, models, or generator handles exist in the module.
- Denylist sanitization (confidence, self-evaluation/assessment, reasoning
  traces, justifications, certainty, …) at any nesting depth; verdicts proven
  invariant to flattering and self-doubting pollution in both directions.
- Static tripwire test bans generator symbols from the evaluator module.
- Grounding judge forced to the deterministic heuristic (`adapter=None`).

## 3. Storage and honesty

- New tables `automated_reviews` / `automated_targets` (migration 0003);
  reviewer identities namespaced `auto_*`; human-path writers refuse automated
  actors and vice versa. Snapshot sections, manifest counts, and registry
  artifact (`auto-review-snapshot`) are separate from the human track.
- Counter: distinct `patient_ref`s, approve/correct only, complete provenance,
  revalidation passed. Live count: **0**.
- Splits by patient (deterministic, stratified); contamination by id +
  near-dup similarity; exported rows machine-checked 100% automated with banned
  human-review phrases.

## 4. FIX-LOOP: DDI engine-shape defect (Phase 4)

- `DrugInteractionRule` expected a bare interactions list but the engine hands
  it the full table document, crashing into a spurious critical on EVERY
  engine evaluation (router could never verify). Fixed with dual-shape
  tolerance (mirroring the contraindication rule); regression test
  `test_engine_with_real_tables_no_spurious_ddi_critical` added to the Step-25
  suite. Dose/red-flags/contraindication rules verified shape-safe.

## 5. Consequences

- Step 41 executes as BLOCKED (0/500) with code+tests ready; unblocks purely
  by accumulating decided automated reviews, no threshold or gate changes.
- `safety_regressions = 0` untouched. No LoRA/training started. H7 still
  requires an owner ruling (physician vs optional/external, per design §I).
