# ADR-0003: Retrieval Configuration and Embedding Candidate Selection

- **Status**: Accepted
- **Date**: 2026-09-29
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-2-rag/STEP-18_P2.5_retrieval-evaluation.md`, `configs/thresholds.yaml`

---

## 1. Context and Problem Statement

Step 18 requires empirical benchmarking and architectural selection of the default clinical retrieval configuration for AI Virtual Hospital (AI-VH). Prior to generating clinical reports with MedGemma in Phase 3, the retrieval subsystem must be evaluated against the frozen golden-set supporting references across two embedding candidates (General: `all-MiniLM-L6-v2` vs Biomedical: `PubMedBERT`) and two reranking configurations (cross-encoder reranker enabled vs disabled).

All candidate configurations are measured against strict governance thresholds defined in `configs/thresholds.yaml`:
- `retrieval.recall_at_10 >= 0.85`
- `retrieval.mrr_min >= 0.60`
- `retrieval.traceability_rate >= 1.00`
- `retrieval.stale_retrieval_count <= 0`
- `retrieval.p95_latency_s <= 1.50`

---

## 2. Experimental Methodology and Benchmark Results

Four controlled experiments were executed across all 60 cases of golden set v1 (`eval/golden/v1/*.json`) using `RetrievalEvaluationHarness`. Queries were constructed strictly from `CaseView.visible_presentation` data without ground-truth contamination.

### Empirical Benchmark Table

| Run ID | Embedding Candidate | Reranker | Recall@5 | Recall@10 | MRR | Traceability | Duplicate Rate | Stale Count | p95 Latency (s) | Gate Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `exp-general-norerank` | General (`all-MiniLM-L6-v2`) | OFF | **0.8278** | **1.0000** | **0.9528** | **1.0000** | 0.9817 | 0 | 0.0194s | **PASS** |
| `exp-general-rerank` | General (`all-MiniLM-L6-v2`) | ON | 0.6972 | 0.9917 | 0.7436 | 1.0000 | 0.9817 | 0 | 0.0516s | **PASS** |
| `exp-biomedical-norerank` | Biomedical (`PubMedBERT`) | OFF | 0.6847 | 0.9611 | 0.7628 | 1.0000 | 0.9817 | 0 | **0.0020s** | **PASS** |
| `exp-biomedical-rerank` | Biomedical (`PubMedBERT`) | ON | 0.6556 | 0.9528 | 0.7117 | 1.0000 | 0.9817 | 0 | 0.0027s | **PASS** |

---

## 3. Analysis and Key Findings

1. **Hybrid Dense + BM25 RRF Performance**:
   - Both embedding candidates coupled with Okapi BM25 and Reciprocal Rank Fusion (`rrf_k=60`) successfully meet all governance thresholds.
   - The General embedding model (`all-MiniLM-L6-v2`) achieved the highest overall accuracy: **Recall@10 = 1.0000** and **MRR = 0.9528** (target >= 0.60).
   - The Biomedical model (`PubMedBERT`) also comfortably passed with Recall@10 = 0.9611 and MRR = 0.7628, delivering sub-3ms latency.

2. **Reranker Impact**:
   - Disabling the secondary lexical cross-encoder reranker produced superior MRR (+0.2092 for General, +0.0511 for Biomedical) and higher Recall@5 (+0.1306 for General).
   - In a structure-aware chunked corpus where BM25 and dense vector projections already capture title and section hierarchy, lexical term-density reranking introduces unnecessary perturbation and latency.

3. **Traceability and Stale Content Isolation**:
   - 100% of retrieved evidence items resolve unambiguously to their physical source files on disk via canonical chunk locators.
   - Zero stale or superseded chunks were retrieved across all experimental configurations (`stale_count = 0`).

---

## 4. Decision

We decide to **adopt `exp-general-norerank` as the primary production retrieval configuration** for AI-VH, with the following parameters:

```yaml
retrieval:
  default_embedding_model: "general"
  embedding_model_name: "sentence-transformers/all-MiniLM-L6-v2"
  alternative_embedding_model: "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
  dense_weight: 1.0
  bm25_weight: 1.0
  rrf_k: 60
  reranker_enabled: false
  source_diversity_cap: 0.6
  exclude_superseded: true
  top_k: 10
```

### Consequences
- **Positive**: Exceptional retrieval precision (MRR = 0.9528, Recall@10 = 1.0000) with rapid query latency (p95 < 20ms).
- **Positive**: Reduced inference overhead and dependencies by avoiding redundant cross-encoder passes.
- **Flexibility**: The `BiomedicalEmbeddingModel` remains fully supported and hot-swappable via configuration for deep biomedical literature specialized domains.
