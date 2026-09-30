# ADR-0010: Agreement Metrics and Snapshot Lineage

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-6-feedback/STEP-39_P6.4_agreement-and-snapshots.md`

---

## 1. Context

P6.4 needs overlap agreement (kappa), error distributions, throughput, and
versioned training-input snapshots with lineage. Only decided sessions count.

## 2. Decision

- Cohen's kappa over paired labels; empty input scores 0.0; unanimous
  marginals score 1.0 on agreement, 0.0 otherwise (chance undefined there).
- Overlap pairs = first two decided sessions per original (oldest first);
  claim pairs restricted to claims both reviewers rated; decisions paired
  as approve/correct/reject labels.
- Error = any rating other than `correct`, broken down per taxonomy code.
- Snapshots reuse the existing `ArtifactRegistry` (kind `dataset`, name
  `feedback-snapshot`): canonical JSONL/JSON (sorted keys, deterministic row
  order), dataset sha over per-file hashes, lineage `{golden_version: v1,
  code_version: git HEAD}`, parent `golden-v1`. Re-running on one store is
  byte-identical except the manifest timestamp.
- Snapshot output (`data/feedback_snapshots/`) is generated and gitignored.

## 3. Consequences

- Phase 7 consumes snapshot directories only; the live feedback DB is never a
  training input (enforced by convention + the P7.G gate, not by locks).
