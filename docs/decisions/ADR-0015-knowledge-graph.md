# ADR-0015: Knowledge Graph Adopted for Retrieval (+0.22 MRR)

- **Status**: Accepted (measured adoption)
- **Date**: 2026-09-30
- **Deciders**: AI Agent (measurement) & experiment rule; owner owns the flag
- **Governing Document**: `plan/prompts/phase-9-advanced/STEP-52_P9.2_knowledge-graph.md`
- **Note**: the prompt names this ADR-0007, but ADR-0007 is already assigned
  (feedback store). This record takes the next free number, ADR-0015.

---

## 1. Experiment

- Graph (`src/vh/rag/kg/`): RxNorm drugs/ingredients/classes, RxNorm +
  safety-table interactions, safety contraindications, specialty conditions,
  guideline documents, and guideline chunks. Every edge carries provenance;
  `verify_graph` + tests prove each edge resolves (formulary, safety rows,
  chunk map, chunker output). Dose/red-flag tables carry no relations and are
  excluded by design. Condition query-term lists are retrieval heuristics.
- Mechanism: query-matched nodes (RxNorm synonyms, condition terms) yield
  reachable guideline chunk ids; base-ranked reachable items get +0.5 and
  re-sort; missing reachable chunks (max 2, built from index records) append;
  truncate to k. Flag `kgraph.enabled` in `configs/rag.yaml` (default was off).
- A/B: same 60 golden cases, corpus, and scorers as STEP-18; only the arm differs.

## 2. Measured result (60/60 cases, deterministic across repeats)

| Metric | RAG-only | KG-augmented | Delta |
| :--- | :--- | :--- | :--- |
| recall@10 (primary) | 0.9611 | 0.9611 | 0.0000 held |
| MRR (primary) | 0.7628 | **0.9783** | **+0.2155** |
| stale_retrieval_count | 0 | 0 | none |
| traceability_rate | 1.0 | 1.0 | held |
| duplicate_rate | low | low | no explosion |
| p95 latency | < 1.5 s | < 1.5 s | within budget |

## 3. Decision

**ADOPT.** Strict MRR improvement (+0.2155) with recall held and zero safety
regression satisfies the prompt's adoption rule, so `kgraph.enabled` is now
`true`. Mechanism reading: boosting mapped guideline chunks that base
retrieval buries raises reciprocal rank without displacing anything relevant.
The committed test suite re-measures the full A/B and asserts the flag
matches the measured decision, so any future reversal flips the test red.
