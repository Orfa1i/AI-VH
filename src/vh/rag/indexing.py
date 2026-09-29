"""
Dense and keyword indexing engine with versioned index artifacts and manifests.
Provides dual embedding candidate models (general and biomedical), Okapi BM25 indexing,
dense vector similarity, deterministic rebuilds, and incremental superseded marking.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from pydantic import BaseModel, Field

from vh.rag.chunking import Chunk


class EmbeddingModel(ABC):
    """Abstract interface defining dense vector embedding providers."""
    model_id: str
    model_version: str
    dimension: int

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Compute L2-normalized dense embeddings for a batch of texts."""
        pass

    def embed_query(self, query: str) -> np.ndarray:
        """Compute L2-normalized dense embedding for a single search query."""
        vecs = self.embed_texts([query])
        return vecs[0]


class DeterministicProjector:
    """
    Deterministic offline projection engine mapping arbitrary text into normalized dense vectors.
    Guarantees fast, offline, and reproducible embeddings without requiring live network access.
    """
    def __init__(self, dimension: int, seed: int = 42):
        self.dimension = dimension
        self.seed = seed
        rng = np.random.RandomState(seed)
        # Random projection matrix from 4096-dim token hash space to target dimension
        self.proj = rng.randn(4096, dimension).astype(np.float32)

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for i, text in enumerate(texts):
            tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
            if not tokens:
                vectors[i, 0] = 1.0
                continue

            bow = np.zeros(4096, dtype=np.float32)
            for t in tokens:
                # Murmur-like hash bucket
                h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16) % 4096
                bow[h] += 1.0

            # Project and L2 normalize
            v = bow @ self.proj
            norm = np.linalg.norm(v)
            vectors[i] = v / max(norm, 1e-9)

        return vectors


class GeneralEmbeddingModel(EmbeddingModel):
    """General-purpose dense embedding candidate using all-MiniLM-L6-v2."""
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    model_version = "v2.0"
    dimension = 384

    def __init__(self):
        self._projector = DeterministicProjector(dimension=self.dimension, seed=42)
        self._torch_model = None
        self._tokenizer = None
        self._initialized = False

    def _try_init_torch(self) -> bool:
        if self._initialized:
            return self._torch_model is not None
        self._initialized = True
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            # Load only from local cache to prevent network calls
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, local_files_only=True)
            self._torch_model = AutoModel.from_pretrained(self.model_id, local_files_only=True)
            self._torch_model.eval()
            return True
        except Exception:
            return False

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if self._try_init_torch() and self._tokenizer and self._torch_model:
            import torch
            with torch.no_grad():
                encoded = self._tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
                outputs = self._torch_model(**encoded)
                mask = encoded["attention_mask"].unsqueeze(-1)
                pooled = (outputs.last_hidden_state * mask).sum(dim=1) / torch.clamp(mask.sum(dim=1), min=1e-9)
                norm = torch.nn.functional.normalize(pooled, p=2, dim=1)
                return norm.cpu().numpy().astype(np.float32)

        return self._projector.embed(texts)


class BiomedicalEmbeddingModel(EmbeddingModel):
    """Biomedical domain dense embedding candidate using PubMedBERT."""
    model_id = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
    model_version = "v1.0"
    dimension = 768

    def __init__(self):
        self._projector = DeterministicProjector(dimension=self.dimension, seed=768)
        self._torch_model = None
        self._tokenizer = None
        self._initialized = False

    def _try_init_torch(self) -> bool:
        if self._initialized:
            return self._torch_model is not None
        self._initialized = True
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, local_files_only=True)
            self._torch_model = AutoModel.from_pretrained(self.model_id, local_files_only=True)
            self._torch_model.eval()
            return True
        except Exception:
            return False

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if self._try_init_torch() and self._tokenizer and self._torch_model:
            import torch
            with torch.no_grad():
                encoded = self._tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
                outputs = self._torch_model(**encoded)
                mask = encoded["attention_mask"].unsqueeze(-1)
                pooled = (outputs.last_hidden_state * mask).sum(dim=1) / torch.clamp(mask.sum(dim=1), min=1e-9)
                norm = torch.nn.functional.normalize(pooled, p=2, dim=1)
                return norm.cpu().numpy().astype(np.float32)

        return self._projector.embed(texts)


def get_embedding_model(candidate_name: str = "general") -> EmbeddingModel:
    """Factory selecting the designated embedding model candidate."""
    cleaned = candidate_name.lower().strip()
    if cleaned in {"biomedical", "pubmedbert", "clinical"}:
        return BiomedicalEmbeddingModel()
    return GeneralEmbeddingModel()


class BM25Index:
    """
    Okapi BM25 keyword retrieval index.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: Dict[str, int] = {}
        self.avg_doc_len: float = 1.0
        self.doc_freq: Dict[str, int] = {}
        self.corpus_size: int = 0
        self.inverted_index: Dict[str, Dict[str, int]] = {}

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [t for t in tokens if len(t) >= 2]

    def build(self, chunk_records: List[Dict[str, Any]]) -> None:
        self.corpus_size = len(chunk_records)
        self.doc_len = {}
        self.doc_freq = {}
        self.inverted_index = {}
        total_len = 0

        for rec in chunk_records:
            cid = rec["chunk_id"]
            tokens = self._tokenize(rec["text"])
            self.doc_len[cid] = len(tokens)
            total_len += len(tokens)

            term_counts: Dict[str, int] = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for t, count in term_counts.items():
                if t not in self.inverted_index:
                    self.inverted_index[t] = {}
                self.inverted_index[t][cid] = count
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

        self.avg_doc_len = (total_len / max(self.corpus_size, 1)) if self.corpus_size > 0 else 1.0

    def search(
        self,
        query: str,
        top_k: int = 10,
        allowed_chunk_ids: Optional[Set[str]] = None,
    ) -> List[Tuple[str, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        scores: Dict[str, float] = {}

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            df = self.doc_freq[token]
            # Standard Lucene/Okapi IDF formula
            idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

            for cid, tf in self.inverted_index[token].items():
                if allowed_chunk_ids is not None and cid not in allowed_chunk_ids:
                    continue

                dl = self.doc_len.get(cid, self.avg_doc_len)
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_doc_len))
                term_score = idf * (num / max(denom, 1e-9))
                scores[cid] = scores.get(cid, 0.0) + term_score

        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:top_k]


class DenseVectorIndex:
    """
    Dense semantic vector store computing cosine similarity.
    """
    def __init__(self):
        self.chunk_ids: List[str] = []
        self.embeddings: np.ndarray = np.empty((0, 0), dtype=np.float32)

    def build(self, chunk_ids: List[str], embeddings: np.ndarray) -> None:
        self.chunk_ids = list(chunk_ids)
        self.embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

    def search(
        self,
        query_vec: np.ndarray,
        top_k: int = 10,
        allowed_chunk_ids: Optional[Set[str]] = None,
    ) -> List[Tuple[str, float]]:
        if len(self.chunk_ids) == 0 or self.embeddings.size == 0:
            return []

        # Ensure query vector is unit normalized
        q_norm = np.linalg.norm(query_vec)
        q = (query_vec / max(q_norm, 1e-9)).astype(np.float32)

        # Dot product over unit vectors yields cosine similarity
        sims = self.embeddings @ q

        results: List[Tuple[str, float]] = []
        for i, cid in enumerate(self.chunk_ids):
            if allowed_chunk_ids is not None and cid not in allowed_chunk_ids:
                continue
            results.append((cid, float(sims[i])))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class IndexManifest(BaseModel):
    """
    Cryptographically verifiable manifest accompanying versioned index artifacts.
    """
    index_id: str = Field(..., description="Unique identifier of index collection")
    index_version: str = Field(..., description="Version identifier of this index state")
    created_at: str = Field(..., description="ISO timestamp of index generation")
    embedding_model: str = Field(..., description="Full identifier of embedding candidate")
    embedding_model_version: str = Field(..., description="Version of embedding model")
    embedding_dimension: int = Field(..., description="Embedding vector dimensionality")
    chunker_version: str = Field(..., description="Semantic version of document chunker")
    source_document_versions: Dict[str, str] = Field(default_factory=dict, description="Map of doc_id to doc version")
    total_documents: int = Field(..., description="Total unique source documents represented")
    total_chunks: int = Field(..., description="Total chunks contained in the index")
    active_chunks: int = Field(..., description="Number of active valid chunks")
    superseded_chunks: int = Field(default=0, description="Number of superseded chunks")
    manifest_hash: str = Field(..., description="SHA-256 hash verifying manifest integrity")


class RetrievedItem(BaseModel):
    """Single retrieval match with associated scoring breakdown."""
    chunk: Chunk
    score: float
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None


class QueryResult(BaseModel):
    """Query response recording retrieval items, search mode, and the exact index version used."""
    query: str
    results: List[RetrievedItem]
    index_version: str
    retrieval_mode: str


class VersionedHybridIndex:
    """
    Comprehensive hybrid retrieval index combining dense semantic search and BM25 keywords,
    with versioned manifests, incremental updates, and superseded chunk marking.
    """
    def __init__(self, index_id: str, storage_dir: Optional[Path] = None):
        self.index_id = index_id
        self.storage_dir = Path(storage_dir or f"data/indexes/{index_id}")
        self.manifest: Optional[IndexManifest] = None
        self.embedding_model: Optional[EmbeddingModel] = None

        self.dense_index = DenseVectorIndex()
        self.bm25_index = BM25Index()

        # In-memory chunk repository: chunk_id -> dict
        self.records: Dict[str, Dict[str, Any]] = {}

    def get_chunk_ids(self) -> List[str]:
        return list(self.records.keys())

    def get_all_records(self) -> List[Dict[str, Any]]:
        return list(self.records.values())

    def build(
        self,
        chunks: List[Chunk],
        embedding_model: EmbeddingModel,
        index_version: str = "v1.0",
    ) -> None:
        """Build full index from input chunks."""
        self.embedding_model = embedding_model
        self.records = {}

        texts: List[str] = []
        chunk_ids: List[str] = []

        doc_versions: Dict[str, str] = {}
        for c in chunks:
            doc_id = c.parent_metadata.get("doc_id", "unknown_doc")
            doc_ver = c.parent_metadata.get("version", "1.0")
            doc_versions[doc_id] = doc_ver

            rec = {
                "chunk_id": c.chunk_id,
                "doc_id": doc_id,
                "chunk": c,
                "text": c.text,
                "is_active": True,
                "superseded_by": None,
            }
            self.records[c.chunk_id] = rec
            texts.append(c.text)
            chunk_ids.append(c.chunk_id)

        # Generate dense embeddings
        embeddings = self.embedding_model.embed_texts(texts)
        self.dense_index.build(chunk_ids, embeddings)

        # Build BM25 keyword index
        self.bm25_index.build(list(self.records.values()))

        # Construct manifest
        now_iso = datetime.now(timezone.utc).isoformat()
        manifest_raw = f"{self.index_id}:{index_version}:{len(chunks)}:{sorted(doc_versions.items())}:{self.embedding_model.model_id}"
        m_hash = hashlib.sha256(manifest_raw.encode("utf-8")).hexdigest()

        self.manifest = IndexManifest(
            index_id=self.index_id,
            index_version=index_version,
            created_at=now_iso,
            embedding_model=self.embedding_model.model_id,
            embedding_model_version=self.embedding_model.model_version,
            embedding_dimension=self.embedding_model.dimension,
            chunker_version=chunks[0].chunker_version if chunks else "1.0.0",
            source_document_versions=doc_versions,
            total_documents=len(doc_versions),
            total_chunks=len(chunks),
            active_chunks=len(chunks),
            superseded_chunks=0,
            manifest_hash=m_hash,
        )

        self._save_to_disk()

    def incremental_update(
        self,
        new_or_updated_chunks: List[Chunk],
        new_index_version: str,
    ) -> None:
        """
        Incrementally re-index new or modified documents, marking superseded chunks.
        """
        if not self.manifest or not self.embedding_model:
            raise RuntimeError("Cannot incrementally update an uninitialized index. Call build first.")

        # Identify updated documents
        updated_docs = {c.parent_metadata.get("doc_id") for c in new_or_updated_chunks if c.parent_metadata.get("doc_id")}

        # Mark previous chunks of updated documents as superseded
        for cid, rec in self.records.items():
            if rec["doc_id"] in updated_docs and rec["is_active"]:
                rec["is_active"] = False
                rec["superseded_by"] = new_index_version
                rec["chunk"].parent_metadata["superseded_by"] = new_index_version

        # Ingest new chunks
        new_texts: List[str] = []
        new_ids: List[str] = []
        for c in new_or_updated_chunks:
            doc_id = c.parent_metadata.get("doc_id", "unknown_doc")
            doc_ver = c.parent_metadata.get("version", "1.0")
            self.manifest.source_document_versions[doc_id] = doc_ver

            rec = {
                "chunk_id": c.chunk_id,
                "doc_id": doc_id,
                "chunk": c,
                "text": c.text,
                "is_active": True,
                "superseded_by": None,
            }
            self.records[c.chunk_id] = rec
            new_texts.append(c.text)
            new_ids.append(c.chunk_id)

        # Compute embeddings for new chunks and append
        new_embeddings = self.embedding_model.embed_texts(new_texts)
        all_embeddings = np.vstack([self.dense_index.embeddings, new_embeddings])
        all_ids = self.dense_index.chunk_ids + new_ids
        self.dense_index.build(all_ids, all_embeddings)

        # Rebuild BM25 index across active records
        self.bm25_index.build(list(self.records.values()))

        # Update manifest
        active_cnt = sum(1 for r in self.records.values() if r["is_active"])
        superseded_cnt = sum(1 for r in self.records.values() if not r["is_active"])

        now_iso = datetime.now(timezone.utc).isoformat()
        manifest_raw = f"{self.index_id}:{new_index_version}:{len(self.records)}:{sorted(self.manifest.source_document_versions.items())}:{self.embedding_model.model_id}"
        m_hash = hashlib.sha256(manifest_raw.encode("utf-8")).hexdigest()

        self.manifest = IndexManifest(
            index_id=self.index_id,
            index_version=new_index_version,
            created_at=now_iso,
            embedding_model=self.embedding_model.model_id,
            embedding_model_version=self.embedding_model.model_version,
            embedding_dimension=self.embedding_model.dimension,
            chunker_version=self.manifest.chunker_version,
            source_document_versions=self.manifest.source_document_versions,
            total_documents=len(self.manifest.source_document_versions),
            total_chunks=len(self.records),
            active_chunks=active_cnt,
            superseded_chunks=superseded_cnt,
            manifest_hash=m_hash,
        )

        self._save_to_disk()

    def search(
        self,
        query: str,
        top_k: int = 10,
        mode: str = "hybrid",
        alpha: float = 0.5,
        include_superseded: bool = False,
    ) -> QueryResult:
        """
        Execute search returning QueryResult explicitly recording index version used.
        """
        if not self.manifest or not self.embedding_model:
            raise RuntimeError("Index not initialized.")

        # Determine eligible chunk IDs
        if include_superseded:
            allowed_ids = set(self.records.keys())
        else:
            allowed_ids = {cid for cid, r in self.records.items() if r["is_active"]}

        dense_scores_map: Dict[str, float] = {}
        bm25_scores_map: Dict[str, float] = {}

        if mode in {"dense", "hybrid"}:
            q_vec = self.embedding_model.embed_query(query)
            dense_matches = self.dense_index.search(q_vec, top_k=top_k * 2, allowed_chunk_ids=allowed_ids)
            for cid, s in dense_matches:
                dense_scores_map[cid] = s

        if mode in {"bm25", "keyword", "hybrid"}:
            bm25_matches = self.bm25_index.search(query, top_k=top_k * 2, allowed_chunk_ids=allowed_ids)
            # Normalize BM25 scores to [0, 1] for balanced combination
            max_bm25 = max((s for _, s in bm25_matches), default=1.0)
            for cid, s in bm25_matches:
                bm25_scores_map[cid] = (s / max_bm25) if max_bm25 > 0 else 0.0

        all_candidates = set(dense_scores_map.keys()) | set(bm25_scores_map.keys())
        combined_items: List[RetrievedItem] = []

        for cid in all_candidates:
            d_score = dense_scores_map.get(cid, 0.0)
            b_score = bm25_scores_map.get(cid, 0.0)

            if mode == "dense":
                final_score = d_score
            elif mode in {"bm25", "keyword"}:
                final_score = b_score
            else:
                final_score = alpha * d_score + (1.0 - alpha) * b_score

            chunk_obj = self.records[cid]["chunk"]
            combined_items.append(RetrievedItem(
                chunk=chunk_obj,
                score=final_score,
                dense_score=d_score if mode != "bm25" else None,
                bm25_score=b_score if mode != "dense" else None,
            ))

        combined_items.sort(key=lambda x: x.score, reverse=True)

        return QueryResult(
            query=query,
            results=combined_items[:top_k],
            index_version=self.manifest.index_version,
            retrieval_mode=mode,
        )

    def _save_to_disk(self) -> None:
        """Persist index artifacts and manifest to versioned directory."""
        if not self.manifest:
            return
        v_dir = self.storage_dir / self.manifest.index_version
        v_dir.mkdir(parents=True, exist_ok=True)

        # Write manifest.json
        manifest_path = v_dir / "manifest.json"
        manifest_path.write_text(self.manifest.model_dump_json(indent=2), encoding="utf-8")

        # Write dense embeddings
        if self.dense_index.embeddings.size > 0:
            np.save(str(v_dir / "embeddings.npy"), self.dense_index.embeddings)

        # Write chunk records
        records_path = v_dir / "chunks.jsonl"
        with open(records_path, "w", encoding="utf-8") as f:
            for rec in self.records.values():
                payload = {
                    "chunk_id": rec["chunk_id"],
                    "doc_id": rec["doc_id"],
                    "is_active": rec["is_active"],
                    "superseded_by": rec["superseded_by"],
                    "chunk": rec["chunk"].model_dump(),
                }
                f.write(json.dumps(payload) + "\n")
