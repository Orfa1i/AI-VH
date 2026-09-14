"""
Medical Knowledge Semantic Retrieval Engine
Provides hybrid BM25 / token-weighted semantic search over medical textbook chunks.
"""

import math
import re
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger("MedicalVectorIndex")


class MedicalKnowledgeIndex:
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_tokens: List[List[str]] = []
        self.doc_freq: Dict[str, int] = {}
        self.avg_doc_len = 0.0
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, retain alphanumeric and hyphenated medical terms
        tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text.lower())
        # Filter very short tokens
        return [t for t in tokens if len(t) > 2]

    def _build_index(self):
        total_len = 0
        for chunk in self.chunks:
            # Combine topic, chapter, and text for rich indexing
            full_text = f"{chunk.get('topic', '')} {chunk.get('chapter', '')} {chunk.get('text', '')}"
            tokens = self._tokenize(full_text)
            self.doc_tokens.append(tokens)
            total_len += len(tokens)

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

        self.avg_doc_len = (total_len / max(self.corpus_size, 1)) if self.corpus_size > 0 else 1.0
        logger.info(f"Indexed {self.corpus_size} medical knowledge chunks (vocab: {len(self.doc_freq)} terms)")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        # BM25 Parameters
        k1 = 1.5
        b = 0.75

        scores: List[Tuple[float, int]] = []

        for idx, doc in enumerate(self.doc_tokens):
            doc_len = len(doc)
            score = 0.0

            # Count token frequencies in document
            tf_map: Dict[str, int] = {}
            for t in doc:
                tf_map[t] = tf_map.get(t, 0) + 1

            for q in query_tokens:
                if q in tf_map:
                    tf = tf_map[q]
                    df = self.doc_freq.get(q, 1)
                    # Robertson-Spärck Jones IDF
                    idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))
                    # BM25 term score
                    denom = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                    score += idf * ((tf * (k1 + 1.0)) / denom)

            if score > 0.0:
                scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_results = []

        for score, idx in scores[:top_k]:
            chunk = self.chunks[idx].copy()
            chunk["relevance_score"] = round(score, 3)
            top_results.append(chunk)

        return top_results
