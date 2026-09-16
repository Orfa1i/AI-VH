"""
Medical Knowledge Semantic Retrieval Engine
Provides hybrid BM25 + dense semantic vector search over medical textbook chunks.
Supports dense embeddings via all-MiniLM-L6-v2 and fast NumPy cosine dot products.
"""

import math
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger("MedicalVectorIndex")


class MedicalKnowledgeIndex:
    def __init__(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: Optional[np.ndarray] = None,
        embeddings_path: Optional[Path] = None,
    ):
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_tokens: List[List[str]] = []
        self.doc_freq: Dict[str, int] = {}
        self.avg_doc_len = 0.0
        self.embeddings: Optional[np.ndarray] = embeddings
        self._embedder = None

        if self.embeddings is None and embeddings_path and embeddings_path.exists():
            try:
                self.embeddings = np.load(str(embeddings_path))
                logger.info(f"Loaded {self.embeddings.shape[0]} dense vector embeddings for hybrid retrieval.")
            except Exception as e:
                logger.warning(f"Could not load precomputed embeddings ({e})")

        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text.lower())
        return [t for t in tokens if len(t) > 2]

    def _build_index(self):
        total_len = 0
        for chunk in self.chunks:
            full_text = f"{chunk.get('topic', '')} {chunk.get('chapter', '')} {chunk.get('text', '')}"
            tokens = self._tokenize(full_text)
            self.doc_tokens.append(tokens)
            total_len += len(tokens)

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

        self.avg_doc_len = (total_len / max(self.corpus_size, 1)) if self.corpus_size > 0 else 1.0
        logger.info(f"Indexed {self.corpus_size} medical knowledge chunks (vocab: {len(self.doc_freq)} terms)")

    def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        try:
            from .vector_embedder import get_vector_embedder
            if self._embedder is None:
                self._embedder = get_vector_embedder()
            vec = self._embedder.embed_query(query)
            if vec:
                return np.array(vec, dtype=np.float32)
        except Exception as e:
            logger.warning(f"Dense query embedding unavailable ({e})")
        return None

    def search(self, query: str, top_k: int = 3, dense_weight: float = 0.6) -> List[Dict[str, Any]]:
        if self.corpus_size == 0:
            return []

        query_tokens = self._tokenize(query)

        # 1. BM25 Scoring
        k1 = 1.5
        b = 0.75
        bm25_scores = np.zeros(self.corpus_size, dtype=np.float32)

        if query_tokens:
            for idx, doc in enumerate(self.doc_tokens):
                doc_len = len(doc)
                score = 0.0
                tf_map: Dict[str, int] = {}
                for t in doc:
                    tf_map[t] = tf_map.get(t, 0) + 1

                for q in query_tokens:
                    if q in tf_map:
                        tf = tf_map[q]
                        df = self.doc_freq.get(q, 1)
                        idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))
                        denom = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                        score += idf * ((tf * (k1 + 1.0)) / denom)

                bm25_scores[idx] = score

        # Normalize BM25 scores to [0, 1]
        max_bm25 = bm25_scores.max() if self.corpus_size > 0 else 0.0
        if max_bm25 > 1e-6:
            bm25_norm = bm25_scores / max_bm25
        else:
            bm25_norm = bm25_scores

        # 2. Dense Cosine Similarity (if vectors available)
        dense_norm = np.zeros(self.corpus_size, dtype=np.float32)
        has_dense = False

        if self.embeddings is not None and len(self.embeddings) == self.corpus_size:
            q_emb = self._get_query_embedding(query)
            if q_emb is not None:
                # Both vectors are L2-normalized, dot product is cosine similarity
                cos_sim = np.dot(self.embeddings, q_emb)
                # Clip negative values
                dense_norm = np.clip(cos_sim, 0.0, 1.0)
                has_dense = True

        # 3. Hybrid Combination
        if has_dense:
            final_scores = (1.0 - dense_weight) * bm25_norm + dense_weight * dense_norm
        else:
            final_scores = bm25_norm

        top_indices = np.argsort(-final_scores)[:top_k]
        top_results = []

        for idx in top_indices:
            score = float(final_scores[idx])
            if score > 0.0 or not top_results:
                chunk = self.chunks[idx].copy()
                chunk["relevance_score"] = round(score * 10.0, 3)
                top_results.append(chunk)

        return top_results
