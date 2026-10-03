"""
Harrison's Principles of Internal Medicine source adapter (Phase 1).

Harrison is the PRIMARY source. All Harrison-specific logic lives ONLY here;
no logic outside this adapter may be Harrison-specific. More sources will be
added later behind the same SourceAdapter.search() interface.

Port notes: metadata handling ported from backend/rag/book_parser.py
(HarrisonParser / MedicalChunk: book, chapter, topic, page). Extended with
nullable edition / chapter_number / chapter_title / section_heading per the
Phase 1 amendment: never guess or fabricate page numbers.

Owner: Software Engineer.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from vh.rag.sources.base import SourceAdapter, SourceDocument, SourceSearchHit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_COLLECTION = REPO_ROOT / "data" / "knowledge" / "harrison_full_collection.json"
DEFAULT_EMBEDDINGS = REPO_ROOT / "data" / "knowledge" / "harrison_embeddings.npy"

# Embedding provenance: harrison_embeddings.npy was built with
# sentence-transformers/all-MiniLM-L6-v2 (384-dim, L2-normalized mean pooling,
# truncation 512) by backend/rag/full_book_embedder.py via
# backend/rag/vector_embedder.py. The query side MUST use the same model +
# pooling (vh.rag.indexing.GeneralEmbeddingModel). Score scale is cosine
# similarity clipped to [0, 1]; the provisional threshold applies to this scale.
EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_EDITION_RE = re.compile(r"(\d+\s*(?:st|nd|rd|th)\s*Edition(?:\s*\(\d{4}\))?)", re.IGNORECASE)
_CHAPTER_NUM_RE = re.compile(r"^\s*(\d+)\b")


def enrich_harrison_metadata(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive nullable Harrison metadata from a collection entry.

    Never fabricates: unknown edition/chapter_number/page become None.
    """
    book = str(entry.get("book") or "")
    chapter = str(entry.get("chapter") or "")
    topic = str(entry.get("topic") or "")
    page_raw = entry.get("page")

    edition: Optional[str] = None
    match = _EDITION_RE.search(book)
    if match:
        edition = match.group(1).strip()

    chapter_number: Optional[str] = None
    chapter_match = _CHAPTER_NUM_RE.search(chapter)
    if chapter_match:
        chapter_number = chapter_match.group(1)

    chapter_title: Optional[str] = chapter.strip() if chapter.strip() else None
    section_heading: Optional[str] = None
    if topic.strip() and topic.strip() != chapter.strip():
        section_heading = topic.strip()

    page: Optional[int] = None
    try:
        if page_raw is not None and str(page_raw).strip() != "":
            page = int(page_raw)
    except (TypeError, ValueError):
        page = None

    return {
        "chunk_id": str(entry.get("id") or ""),
        "edition": edition,
        "chapter_number": chapter_number,
        "chapter_title": chapter_title,
        "section_heading": section_heading,
        "page": page,
        "book": book,
        "topic": topic,
    }


def entry_to_document(entry: Dict[str, Any]) -> SourceDocument:
    """Convert one harrison_full_collection.json entry to a SourceDocument."""
    meta = enrich_harrison_metadata(entry)
    chunk_id = meta["chunk_id"] or str(entry.get("id") or "unknown")
    chapter_title = meta["chapter_title"] or "Harrison's Principles of Internal Medicine"
    section = [chapter_title]
    if meta["section_heading"]:
        section.append(str(meta["section_heading"]))

    locator = f"harrison:{chunk_id}"
    if meta["page"] is not None:
        locator = f"harrison:{chunk_id}#page-{meta['page']}"

    return SourceDocument(
        source_id="harrison",
        doc_id=chunk_id,
        title=chapter_title,
        section_path=section,
        locator=locator,
        version="21st-2022",
        published_or_updated_date="2022-01-01",
        evidence_level="textbook",
        licence="proprietary-textbook-local-use",
        text=str(entry.get("text") or ""),
        metadata={
            "book": meta["book"],
            "topic": meta["topic"],
            "char_length": len(str(entry.get("text") or "")),
        },
        edition=meta["edition"],
        chapter_number=meta["chapter_number"],
        chapter_title=meta["chapter_title"],
        section_heading=meta["section_heading"],
        page=meta["page"],
    )


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class HarrisonAdapter(SourceAdapter):
    """
    Harrison source adapter behind the common search() interface.

    Retrieval is semantic-first: cosine similarity against the existing
    harrison_embeddings.npy (same all-MiniLM-L6-v2 model + pooling as the
    builder), with a lexical-overlap rerank over the top semantic candidates
    (hybrid). The reported score is always cosine similarity clipped to
    [0, 1]. Pure lexical search runs ONLY as a fallback when the embeddings
    or the real model are unavailable (e.g. unit tests on mini-collections).
    """

    source_id = "harrison"

    def __init__(
        self,
        collection_path: Optional[Path] = None,
        embeddings_path: Optional[Path] = None,
    ) -> None:
        self.collection_path = Path(collection_path) if collection_path else DEFAULT_COLLECTION
        self.embeddings_path = Path(embeddings_path) if embeddings_path else DEFAULT_EMBEDDINGS
        self._entries: Optional[List[Dict[str, Any]]] = None
        self._docs: Optional[List[SourceDocument]] = None
        self._embeddings: Any = None
        self._embeddings_ok: Optional[bool] = None
        self._query_model: Any = None
        self._query_model_ok: Optional[bool] = None

    def _load_entries(self) -> List[Dict[str, Any]]:
        if self._entries is None:
            with open(self.collection_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = list(data) if isinstance(data, list) else []
        return self._entries

    def load_all(self) -> List[SourceDocument]:
        """Load the full Harrison collection as SourceDocuments."""
        if self._docs is None:
            self._docs = [entry_to_document(e) for e in self._load_entries()]
        return list(self._docs)

    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """Parse raw collection entries (list of dicts) into SourceDocuments."""
        if isinstance(raw_content, list):
            return [entry_to_document(e) for e in raw_content if isinstance(e, dict)]
        if isinstance(raw_content, dict):
            return [entry_to_document(raw_content)]
        return []

    def search(self, query: str, top_k: int = 6) -> List[SourceSearchHit]:
        """
        Hybrid semantic + lexical-rerank search over the Harrison collection.

        Score scale: cosine similarity clipped to [0, 1] (embeddings and query
        vector are L2-normalized). Returns at most top_k hits.
        """
        top_k = max(1, min(int(top_k), 8))
        query_tokens = set(_tokenize(query or ""))
        if not query_tokens:
            return []

        entries = self._load_entries()
        cosine = self._cosine_scores(query)
        if cosine is not None:
            return self._hybrid_hits(entries, query_tokens, cosine, top_k)
        return self._lexical_fallback_hits(entries, query_tokens, top_k)

    def _cosine_scores(self, query: str) -> Optional[Any]:
        """Cosine similarity vector over collection rows, or None if unavailable."""
        embeddings = self._load_embeddings()
        if embeddings is None:
            return None
        query_vec = self._embed_query(query)
        if query_vec is None:
            return None
        try:
            import numpy as np

            scores = np.asarray(embeddings, dtype=np.float32) @ np.asarray(query_vec, dtype=np.float32)
            return np.clip(scores, 0.0, 1.0)
        except Exception:
            return None

    def _load_embeddings(self) -> Optional[Any]:
        """Memory-mapped read of the existing .npy (never written by this adapter)."""
        if self._embeddings_ok is False:
            return None
        if self._embeddings is None:
            try:
                import numpy as np

                if not self.embeddings_path.exists():
                    self._embeddings_ok = False
                    return None
                matrix = np.load(str(self.embeddings_path), mmap_mode="r")
                entries = self._load_entries()
                if matrix.shape != (len(entries), EMBEDDING_DIM):
                    self._embeddings_ok = False
                    return None
                self._embeddings = matrix
                self._embeddings_ok = True
            except Exception:
                self._embeddings_ok = False
                return None
        return self._embeddings

    def _embed_query(self, query: str) -> Optional[Any]:
        """Embed with the SAME model + pooling as the builder; None on fallback."""
        if self._query_model_ok is False:
            return None
        try:
            if self._query_model is None:
                from vh.rag.indexing import get_embedding_model

                model = get_embedding_model("general")
                if getattr(model, "model_id", "") != EMBEDDING_MODEL_ID:
                    self._query_model_ok = False
                    return None
                # Real torch model required: the deterministic projector fallback
                # lives in a different vector space and must never score real rows.
                init = getattr(model, "_try_init_torch", None)
                if callable(init) and not init():
                    self._query_model_ok = False
                    return None
                if getattr(model, "_torch_model", None) is None:
                    self._query_model_ok = False
                    return None
                self._query_model = model
                self._query_model_ok = True
            vecs = self._query_model.embed_texts([query])
            if vecs is None or len(vecs) == 0:
                return None
            return vecs[0]
        except Exception:
            self._query_model_ok = False
            return None

    def _hybrid_hits(self, entries: List[Dict[str, Any]], query_tokens: Any, cosine: Any, top_k: int) -> List[SourceSearchHit]:
        """Semantic candidates reranked by lexical overlap; score stays cosine."""
        import numpy as np

        pool = max(top_k * 4, 20)
        order = np.argsort(-np.asarray(cosine)).tolist()[:pool]
        ranked = []
        for idx in order:
            entry = entries[int(idx)]
            text = f"{entry.get('topic', '')} {entry.get('chapter', '')} {entry.get('text', '')}"
            overlap = len(query_tokens & set(_tokenize(text)))
            ranked.append((float(cosine[int(idx)]), overlap, int(idx)))
        # Hybrid rerank: cosine first, lexical overlap breaks near-ties.
        ranked.sort(key=lambda t: (round(t[0], 4), t[1]), reverse=True)
        hits: List[SourceSearchHit] = []
        for cos_score, overlap, idx in ranked[:top_k]:
            entry = entries[idx]
            meta = enrich_harrison_metadata(entry)
            meta["retrieval_mode"] = "semantic-hybrid"
            meta["lexical_overlap"] = overlap
            hits.append(
                SourceSearchHit(
                    source_name="harrison",
                    chunk_id=str(entry.get("id") or ""),
                    metadata=meta,
                    text=str(entry.get("text") or ""),
                    score=float(cos_score),
                )
            )
        return hits

    def _lexical_fallback_hits(
        self, entries: List[Dict[str, Any]], query_tokens: Any, top_k: int
    ) -> List[SourceSearchHit]:
        """
        Test-only fallback: token-overlap ratio in [0, 1].

        Runs only when the embeddings or the real embedding model is
        unavailable. Every hit is tagged retrieval_mode=lexical-fallback.
        """
        scored: List[SourceSearchHit] = []
        for entry in entries:
            text = f"{entry.get('topic', '')} {entry.get('chapter', '')} {entry.get('text', '')}"
            doc_tokens = set(_tokenize(text))
            if not doc_tokens:
                continue
            overlap = len(query_tokens & doc_tokens)
            if overlap == 0:
                continue
            score = overlap / max(len(query_tokens), 1)
            meta = enrich_harrison_metadata(entry)
            meta["retrieval_mode"] = "lexical-fallback"
            scored.append(
                SourceSearchHit(
                    source_name="harrison",
                    chunk_id=str(entry.get("id") or ""),
                    metadata=meta,
                    text=str(entry.get("text") or ""),
                    score=float(score),
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]
