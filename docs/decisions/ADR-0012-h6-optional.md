# ADR-0012: H6 Reclassified as Optional External Validation

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Project Owner (policy) & AI Agent (implementation)
- **Governing Documents**: updated `plan/README.md`, `plan/prompts/phase-6-feedback/STEP-40_P6.G_gate.md`

---

## 1. Context

The H6 gate required 2-3 real doctors reviewing reports in the live UI plus a
human-written sign-off. That requirement does not apply to the AI-V execution
path: the Virtual Hospital must operate without real doctors in the
simulation/runtime. No H6 evidence, reviews, signatures, findings, or
sign-offs were fabricated to reach this decision; `docs/signoffs/H6-usability.md`
does not exist and was not created.

## 2. Decision

- H6 is an OPTIONAL / EXTERNAL VALIDATION milestone, not a blocking
  implementation gate and not a prerequisite for STEP 40 or Phase 6.
- The STEP 40 gate evaluates an automated substitute instead:
  - **Automated system validation**: full regression, harness eval, overlap
    mechanism proof, agreement-pipeline unit proof.
  - **Synthetic-case evaluation**: encounter pipeline over golden v1 scored
    against Ground Truth (mean vs `agents.encounter_score_min`), re-measured
    at gate time; explicitly not physician judgment.
- Three tiers are stated separately in every gate report; physician usability
  is documented as future/external work and never claimed.
- `review.kappa_min`: pipeline correctness proven on known-value fixtures;
  kappa recorded UNMEASURED (no overlap review data), never a pass on agreement.

## 3. Consequences

- Phase 6 can certify on automated evidence. If H6 is ever performed
  externally, its sign-off lives at `docs/signoffs/H6-usability.md` and is
  never a retroactive gate input unless the owner reinstates it.
