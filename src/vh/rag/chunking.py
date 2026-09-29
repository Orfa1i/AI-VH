"""
Structure-aware clinical document chunking engine.
Splits on document structure first (SPL, PMC, guidelines, abstracts) and preserves tables and lists.
Enforces strict character offset integrity and deterministic hashing.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from vh.rag.sources.base import SourceDocument


def count_tokens(text: str) -> int:
    """
    Fast and deterministic token approximation counting words and punctuation symbols.
    """
    if not text:
        return 0
    return len(re.findall(r"\w+|[^\w\s]", text))


class ChunkerConfig(BaseModel):
    """Configuration settings for structure-aware document chunking."""
    target_chunk_tokens: int = Field(default=256, description="Target token budget per chunk")
    max_chunk_tokens: int = Field(default=384, description="Hard ceiling for standard chunk tokens")
    overlap_tokens: int = Field(default=32, description="Token overlap between consecutive chunks")
    chunker_version: str = Field(default="1.0.0", description="Semantic version of chunking algorithm")
    preserve_tables: bool = Field(default=True, description="Keep markdown tables whole")
    preserve_lists: bool = Field(default=True, description="Keep lists whole when possible")


class Chunk(BaseModel):
    """
    Normalised chunk representing an evidence unit traceable back to exact source text.
    """
    chunk_id: str = Field(..., description="Deterministic cryptographic hash of chunk provenance")
    text: str = Field(..., description="Exact textual slice from normalized parent document")
    token_count: int = Field(..., description="Calculated token count of chunk text")
    section_path: List[str] = Field(default_factory=list, description="Document section hierarchy")
    locator: str = Field(..., description="Canonical locator with offset anchor")
    start_char_offset: int = Field(..., description="Starting character index into parent doc.text")
    end_char_offset: int = Field(..., description="Ending character index into parent doc.text")
    chunker_version: str = Field(..., description="Chunker version utilized for extraction")
    exceeds_bounds: bool = Field(default=False, description="Flag indicating atomic structural block exceeding bounds")
    parent_metadata: Dict[str, Any] = Field(default_factory=dict, description="Provenance metadata from parent")


class StructureAwareChunker:
    """
    Structure-aware chunker operating across clinical guidelines, SPL labels, and literature.
    """
    def __init__(self, config: Optional[ChunkerConfig] = None):
        self.config = config or ChunkerConfig()

    def chunk_documents(self, documents: List[SourceDocument]) -> List[Chunk]:
        """Process a sequence of SourceDocuments into chunks, preserving section isolation."""
        all_chunks: List[Chunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

    def chunk_document(self, doc: SourceDocument) -> List[Chunk]:
        """
        Split a single SourceDocument into bounded chunks.
        Guarantees:
        1. No chunk crosses the document's section boundary.
        2. doc.text[chunk.start_char_offset:chunk.end_char_offset] == chunk.text exactly.
        3. Deterministic chunk IDs.
        """
        text = doc.text
        if not text or not text.strip():
            return []

        # Identify structural blocks within text (tables, lists, paragraphs)
        blocks = self._identify_structural_blocks(text)
        chunks: List[Chunk] = []

        i = 0
        while i < len(blocks):
            block_start, block_end, block_type = blocks[i]
            block_raw = text[block_start:block_end]
            block_tokens = count_tokens(block_raw)

            # If atomic table exceeds max bounds, preserve it whole and flag it
            if block_type == "table" and self.config.preserve_tables and block_tokens > self.config.max_chunk_tokens:
                c_start, c_end, c_text = self._trim_offsets(text, block_start, block_end)
                chunks.append(self._create_chunk(
                    doc=doc,
                    start=c_start,
                    end=c_end,
                    text=c_text,
                    exceeds_bounds=True,
                ))
                i += 1
                continue

            # If atomic list exceeds max bounds, preserve whole and flag it
            if block_type == "list" and self.config.preserve_lists and block_tokens > self.config.max_chunk_tokens:
                c_start, c_end, c_text = self._trim_offsets(text, block_start, block_end)
                chunks.append(self._create_chunk(
                    doc=doc,
                    start=c_start,
                    end=c_end,
                    text=c_text,
                    exceeds_bounds=True,
                ))
                i += 1
                continue

            # If single paragraph exceeds max bounds, split into sentence-level spans
            if block_tokens > self.config.max_chunk_tokens:
                para_chunks = self._chunk_large_block(doc, text, block_start, block_end)
                chunks.extend(para_chunks)
                i += 1
                continue

            # Accumulate smaller blocks up to target_chunk_tokens
            accum_start = block_start
            accum_end = block_end
            accum_tokens = block_tokens
            next_idx = i + 1

            while next_idx < len(blocks):
                nxt_start, nxt_end, nxt_type = blocks[next_idx]
                nxt_raw = text[nxt_start:nxt_end]
                nxt_tokens = count_tokens(nxt_raw)

                # Stop accumulating if adding next block exceeds max_chunk_tokens
                if accum_tokens + nxt_tokens > self.config.max_chunk_tokens:
                    break

                # Stop accumulating if next block is an oversized atomic table
                if nxt_type == "table" and nxt_tokens > self.config.max_chunk_tokens:
                    break

                accum_end = nxt_end
                accum_tokens += nxt_tokens
                next_idx += 1

                # If we reached target, break cleanly
                if accum_tokens >= self.config.target_chunk_tokens:
                    break

            c_start, c_end, c_text = self._trim_offsets(text, accum_start, accum_end)
            if c_text:
                chunks.append(self._create_chunk(
                    doc=doc,
                    start=c_start,
                    end=c_end,
                    text=c_text,
                    exceeds_bounds=False,
                ))

            i = next_idx

        return chunks

    def _chunk_large_block(
        self,
        doc: SourceDocument,
        full_text: str,
        start_idx: int,
        end_idx: int,
    ) -> List[Chunk]:
        """Split a large paragraph or block into bounded sentence spans with token overlap."""
        block_text = full_text[start_idx:end_idx]
        sentence_spans = self._split_sentence_spans(block_text, start_idx)
        if not sentence_spans:
            c_start, c_end, c_text = self._trim_offsets(full_text, start_idx, end_idx)
            return [self._create_chunk(doc, c_start, c_end, c_text, exceeds_bounds=True)]

        chunks: List[Chunk] = []
        curr_spans: List[Tuple[int, int]] = []
        curr_tokens = 0

        j = 0
        while j < len(sentence_spans):
            s_start, s_end = sentence_spans[j]
            s_tokens = count_tokens(full_text[s_start:s_end])

            if curr_spans and (curr_tokens + s_tokens > self.config.max_chunk_tokens):
                # Emit current accumulated chunk
                span_start = curr_spans[0][0]
                span_end = curr_spans[-1][1]
                c_start, c_end, c_text = self._trim_offsets(full_text, span_start, span_end)
                chunks.append(self._create_chunk(doc, c_start, c_end, c_text, exceeds_bounds=False))

                # Handle overlap: retain trailing spans for overlap
                overlap_spans: List[Tuple[int, int]] = []
                overlap_tokens = 0
                for prev_s_start, prev_s_end in reversed(curr_spans):
                    t_count = count_tokens(full_text[prev_s_start:prev_s_end])
                    if overlap_tokens + t_count <= self.config.overlap_tokens:
                        overlap_spans.insert(0, (prev_s_start, prev_s_end))
                        overlap_tokens += t_count
                    else:
                        break

                curr_spans = overlap_spans
                curr_tokens = overlap_tokens

            curr_spans.append((s_start, s_end))
            curr_tokens += s_tokens
            j += 1

        if curr_spans:
            span_start = curr_spans[0][0]
            span_end = curr_spans[-1][1]
            c_start, c_end, c_text = self._trim_offsets(full_text, span_start, span_end)
            if c_text:
                chunks.append(self._create_chunk(doc, c_start, c_end, c_text, exceeds_bounds=False))

        return chunks

    def _identify_structural_blocks(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Partition text into structural blocks: table, list, or paragraph.
        Returns list of (start_idx, end_idx, block_type).
        """
        blocks: List[Tuple[int, int, str]] = []
        lines = text.splitlines(keepends=True)

        curr_start = 0
        curr_type: Optional[str] = None
        accum_lines: List[str] = []

        line_start_idx = 0
        for line in lines:
            line_len = len(line)
            stripped = line.strip()

            if not stripped:
                # Blank line triggers flush of paragraph or list
                if accum_lines and curr_type:
                    block_end = line_start_idx
                    blocks.append((curr_start, block_end, curr_type))
                    accum_lines = []
                    curr_type = None
                line_start_idx += line_len
                continue

            # Determine line type
            if stripped.startswith("|") and stripped.endswith("|"):
                l_type = "table"
            elif re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
                l_type = "list"
            else:
                l_type = "para"

            if curr_type is None:
                curr_type = l_type
                curr_start = line_start_idx
                accum_lines.append(line)
            elif curr_type == l_type:
                accum_lines.append(line)
            else:
                # Type change: flush previous block
                block_end = line_start_idx
                blocks.append((curr_start, block_end, curr_type))
                curr_type = l_type
                curr_start = line_start_idx
                accum_lines = [line]

            line_start_idx += line_len

        # Flush remaining lines
        if accum_lines and curr_type:
            blocks.append((curr_start, len(text), curr_type))

        return blocks

    def _split_sentence_spans(self, text: str, offset: int) -> List[Tuple[int, int]]:
        """Identify start and end character offsets for sentences within text."""
        spans: List[Tuple[int, int]] = []
        pattern = re.compile(r'([^.!?]+[.!?]+(?:\s+|$)|[^.!?]+$)')
        for match in pattern.finditer(text):
            m_str = match.group(0)
            if m_str.strip():
                s_start = offset + match.start()
                s_end = offset + match.end()
                spans.append((s_start, s_end))
        return spans

    def _trim_offsets(self, text: str, start: int, end: int) -> Tuple[int, int, str]:
        """Trim surrounding whitespace while preserving exact offset mapping."""
        sub = text[start:end]
        l_strip = len(sub) - len(sub.lstrip())
        r_strip = len(sub) - len(sub.rstrip())
        real_start = start + l_strip
        real_end = end - r_strip
        real_text = text[real_start:real_end]
        return real_start, real_end, real_text

    def _create_chunk(
        self,
        doc: SourceDocument,
        start: int,
        end: int,
        text: str,
        exceeds_bounds: bool,
    ) -> Chunk:
        """Create normalized Chunk with deterministic provenance ID and locator anchor."""
        raw_key = f"{doc.source_id}:{doc.doc_id}:{doc.version}:{doc.locator}:{start}:{end}:{self.config.chunker_version}"
        chunk_id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

        locator_anchor = f"{doc.locator}#offset-{start}-{end}"
        token_count = count_tokens(text)

        parent_meta = {
            "source_id": doc.source_id,
            "doc_id": doc.doc_id,
            "title": doc.title,
            "version": doc.version,
            "published_or_updated_date": doc.published_or_updated_date,
            "evidence_level": doc.evidence_level,
            "licence": doc.licence,
            "custom_meta": doc.metadata,
        }

        return Chunk(
            chunk_id=chunk_id,
            text=text,
            token_count=token_count,
            section_path=list(doc.section_path),
            locator=locator_anchor,
            start_char_offset=start,
            end_char_offset=end,
            chunker_version=self.config.chunker_version,
            exceeds_bounds=exceeds_bounds,
            parent_metadata=parent_meta,
        )
