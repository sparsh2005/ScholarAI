"""Embedding service for vector representations.

Uses sentence-transformers for local embeddings with support for
various models optimized for different use cases.

Default model: all-MiniLM-L6-v2
- 384 dimensions
- Fast inference
- Good quality for semantic search
"""

import logging
from typing import Optional
import numpy as np

from config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings.
    
    Uses sentence-transformers library for local embedding generation.
    The model is lazily loaded on first use to avoid startup overhead.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._model = None
        self._dimension: Optional[int] = None
    
    @property
    def model(self):
        """Lazy-load the embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.settings.embedding_model}")
            
            try:
                from sentence_transformers import SentenceTransformer
                
                self._model = SentenceTransformer(self.settings.embedding_model)
                
                # Cache the dimension
                test_embedding = self._model.encode("test", convert_to_numpy=True)
                self._dimension = len(test_embedding)
                
                logger.info(f"Embedding model loaded. Dimension: {self._dimension}")
                
            except ImportError:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                raise ImportError("sentence-transformers is required for embedding generation")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        
        return self._model
    
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed (should be under model's max length)
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.get_embedding_dimension()
        
        # Truncate if too long (most models have 512 token limit)
        if len(text) > 8000:  # Rough character limit
            text = text[:8000]
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        More efficient than calling embed_text() multiple times
        due to batched GPU/CPU operations.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (same order as input)
        """
        if not texts:
            return []
        
        # Filter and track empty texts
        processed_texts = []
        empty_indices = set()
        
        for i, text in enumerate(texts):
            if not text or not text.strip():
                empty_indices.add(i)
                processed_texts.append("placeholder")  # Will be replaced
            else:
                # Truncate if needed
                processed_texts.append(text[:8000] if len(text) > 8000 else text)
        
        # Generate embeddings in batch
        embeddings = self.model.encode(
            processed_texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 50,  # Show progress for large batches
        )
        
        # Convert to list and replace empty text embeddings with zero vectors
        result = []
        dimension = self.get_embedding_dimension()
        
        for i, emb in enumerate(embeddings):
            if i in empty_indices:
                result.append([0.0] * dimension)
            else:
                result.append(emb.tolist())
        
        return result
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        if self._dimension is None:
            # Force model load to get dimension
            _ = self.model
        return self._dimension or 384  # Default for all-MiniLM-L6-v2
    
    def compute_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
