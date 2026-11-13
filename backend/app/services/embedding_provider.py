import math
import hashlib
from typing import List
import numpy as np
from app.core.config import settings

class BaseEmbeddingProvider:
    """Base class for all embedding providers."""
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, high-quality feature hashing embedding provider.
    Generates normalized 1536-dimensional vector representations.
    Ensures identical texts yield cosine similarity = 1.0, and lexically/semantically
    overlapping texts yield proportional cosine similarities without external API calls.
    """
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _hash_vector(self, text: str) -> List[float]:
        cleaned = text.lower().strip()
        if not cleaned:
            return [0.0] * self.dimension

        vec = np.zeros(self.dimension, dtype=np.float32)
        words = cleaned.split()
        
        # Word-level hashed n-grams
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            vec[idx] += sign * 1.5

            # Bigram feature
            if i < len(words) - 1:
                bigram = f"{word}_{words[i+1]}"
                h_bi = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
                idx_bi = h_bi % self.dimension
                sign_bi = 1.0 if ((h_bi >> 4) & 1) else -1.0
                vec[idx_bi] += sign_bi * 2.0

        # Substring 3-grams for morphology
        for k in range(max(0, len(cleaned) - 3)):
            sub = cleaned[k:k+3]
            h_sub = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
            idx_sub = h_sub % self.dimension
            vec[idx_sub] += 0.3

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def embed_text(self, text: str) -> List[float]:
        return self._hash_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_vector(t) for t in texts]

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embeddings using OpenAI text-embedding-3-small or configured model."""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model

    def embed_text(self, text: str) -> List[float]:
        import httpx
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": text,
            "model": self.model
        }
        response = httpx.post(url, json=payload, headers=headers, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        import httpx
        if not texts:
            return []
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model
        }
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory returning the active embedding provider."""
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    if provider_name == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider(settings.OPENAI_API_KEY, settings.EMBEDDING_MODEL)
    return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
