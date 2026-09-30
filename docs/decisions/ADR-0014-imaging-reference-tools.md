# ADR-0014: Reference Imaging Tools over Synthetic Phantoms

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-9-advanced/STEP-51_P9.1_imaging-tools.md`

---

## 1. Context

STEP-51 assumes existing fracture/KOA models plus a licensed de-identified
image dataset. Neither exists in this repository, and repo rules forbid
fetching patient-derived data or running live-network training inside the
verification suite.

## 2. Decision

- Ship deterministic REFERENCE tools (`fracture-loc-ref/v1.0.0`,
  `knee-oa-grade-ref/v1.0.0`) validated against procedural synthetic phantoms
  with known ground truth (seeded numpy, documented geometry). This validates
  the full integration path (typed outputs, permission gating, citation
  enforcement, stub replacement) without pretending to be clinical-grade models.
- Every output carries `interpretation: "model-output"` and a stable
  `IMG-<tool>-<hash8>` evidence id. Real trained-weight integration (dataset
  licence + weights + revalidation) is explicitly recorded as future work.
- Imaging-evidence rule: claims mentioning imaging must cite a known IMG- id
  (`RULE-IMAGING-CITE-001`, major severity, fail-closed on unknown tool sets).
- The P5.2 `NotImplementedError` stub is retired by explicit plan directive;
  the Step-32 assertion was replaced with equal-or-stronger tool behavior
  checks (not weakened).
