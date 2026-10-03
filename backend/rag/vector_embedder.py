"""
Medical Vector Embedder using all-MiniLM-L6-v2 on RTX 4060 GPU
Generates dense 384-dimensional semantic embeddings for Harrison's Internal Medicine RAG.
"""

import logging
from typing import List, Optional
import torch

logger = logging.getLogger("VectorEmbedder")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_global_embedder = None


class MedicalVectorEmbedder:
    def __init__(self, model_name: str = MODEL_NAME, device: Optional[str] = None):
        from transformers import AutoTokenizer, AutoModel

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing MedicalVectorEmbedder ({model_name}) on device: {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            self.model = AutoModel.from_pretrained(model_name, local_files_only=True).to(self.device)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.embedding_dim = self.model.config.hidden_size
        logger.info(f"MedicalVectorEmbedder ready. Dimension: {self.embedding_dim}")

    def embed_texts(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """Computes dense normalized embeddings in batches on GPU."""
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**encoded)
                attention_mask = encoded["attention_mask"].unsqueeze(-1)
                token_embeddings = outputs.last_hidden_state
                # Mean Pooling
                sum_embeddings = torch.sum(token_embeddings * attention_mask, dim=1)
                sum_mask = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
                pooled = sum_embeddings / sum_mask
                # L2 Normalize
                normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)

            all_embeddings.extend(normalized.cpu().tolist())

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Computes dense normalized embedding for a single clinical query."""
        results = self.embed_texts([query], batch_size=1)
        return results[0] if results else []


def get_vector_embedder() -> MedicalVectorEmbedder:
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = MedicalVectorEmbedder()
    return _global_embedder
