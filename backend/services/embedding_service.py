"""Embedding service for vector representations.

Uses sentence-transformers for local embeddings, with optional
OpenAI embeddings for production use.
"""

from typing import Optional
import numpy as np

from config import get_settings


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.settings = get_settings()
        self._model = None
    
    @property
    def model(self):
        """Lazy-load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.settings.embedding_model)
        return self._model
    
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        # Embed a test string to get dimension
        test_embedding = self.embed_text("test")
        return len(test_embedding)
