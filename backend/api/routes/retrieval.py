"""Chunk retrieval API routes.

POST /api/retrieve-chunks - Retrieve relevant chunks via vector search

This module implements the RAG retrieval stage:
1. Query expansion for better recall
2. Semantic vector search
3. Re-ranking for precision
4. Source diversity enforcement
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    RetrieveChunksRequest,
    RetrieveChunksResponse,
    RetrievedChunk,
)
from services.vector_store import VectorStoreService
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retrieve-chunks", tags=["retrieval"])

# Singleton services
_vector_store: Optional[VectorStoreService] = None
_embedding_service: Optional[EmbeddingService] = None


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


def get_embedding_service() -> EmbeddingService:
    """Dependency to get embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


@router.post("", response_model=RetrieveChunksResponse)
async def retrieve_chunks(
    request: RetrieveChunksRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrieveChunksResponse:
    """
    Retrieve relevant document chunks using semantic search with re-ranking.
    
    This endpoint implements a multi-stage retrieval pipeline:
    
    1. **Query Processing**: Clean and normalize the query
    2. **Initial Retrieval**: Fetch top-k*2 candidates via vector similarity
    3. **Re-ranking**: Score candidates by relevance and diversity
    4. **Source Balancing**: Ensure diverse source representation
    5. **Final Selection**: Return top-k highest-quality chunks
    
    The retrieved chunks are used for claim extraction in the next pipeline step.
    
    Request Body:
    ```json
    {
        "session_id": "uuid",
        "query": "Research question",
        "top_k": 10,
        "filters": {"document_id": "optional-filter"}
    }
    ```
    
    Returns chunks sorted by relevance with source attribution.
    """
    logger.info(f"Retrieval request for session {request.session_id}: {request.query[:100]}...")
    
    try:
        # Verify session exists
        session_exists = await vector_store.session_exists(request.session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found. Process documents first."
            )
        
        # Stage 1: Initial retrieval with oversampling for re-ranking
        oversample_factor = 2
        initial_top_k = min(request.top_k * oversample_factor, 50)
        
        results = await vector_store.search(
            session_id=request.session_id,
            query=request.query,
            top_k=initial_top_k,
            filters=request.filters,
        )
        
        if not results:
            logger.info("No results found for query")
            return RetrieveChunksResponse(
                success=True,
                query=request.query,
                chunks=[],
                total_results=0,
            )
        
        # Stage 2: Re-rank and diversify results
        reranked = _rerank_results(results, request.query, embedding_service)
        
        # Stage 3: Ensure source diversity
        diversified = _ensure_source_diversity(reranked, request.top_k)
        
        # Stage 4: Transform to response format
        chunks = [
            RetrievedChunk(
                id=r["id"],
                document_id=r["document_id"],
                source_title=r["source_title"],
                content=r["content"],
                relevance_score=r["relevance_score"],
                metadata=r.get("metadata", {}),
            )
            for r in diversified[:request.top_k]
        ]
        
        logger.info(f"Retrieved {len(chunks)} chunks from {len(set(c.document_id for c in chunks))} sources")
        
        return RetrieveChunksResponse(
            success=True,
            query=request.query,
            chunks=chunks,
            total_results=len(chunks),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )


def _rerank_results(
    results: list[dict],
    query: str,
    embedding_service: EmbeddingService,
) -> list[dict]:
    """
    Re-rank results using multiple signals.
    
    Scoring factors:
    - Vector similarity (primary)
    - Content length (prefer substantial chunks)
    - Section relevance (boost if section title matches query)
    """
    query_lower = query.lower()
    query_terms = set(query_lower.split())
    
    scored_results = []
    for result in results:
        # Base score from vector similarity
        base_score = result["relevance_score"]
        
        # Content quality boost
        content = result["content"]
        content_length = len(content)
        
        # Prefer chunks with substantial content (not too short, not too long)
        if 200 <= content_length <= 1000:
            length_boost = 1.05
        elif content_length < 100:
            length_boost = 0.9
        else:
            length_boost = 1.0
        
        # Keyword overlap boost
        content_lower = content.lower()
        keyword_matches = sum(1 for term in query_terms if term in content_lower)
        keyword_boost = 1 + (keyword_matches * 0.02)  # Small boost per keyword
        
        # Section title relevance boost
        section_title = result.get("metadata", {}).get("section_title", "")
        if section_title:
            section_lower = section_title.lower()
            if any(term in section_lower for term in query_terms):
                section_boost = 1.1
            else:
                section_boost = 1.0
        else:
            section_boost = 1.0
        
        # Combined score
        final_score = base_score * length_boost * keyword_boost * section_boost
        
        result["relevance_score"] = round(min(final_score, 100), 2)
        scored_results.append(result)
    
    # Sort by final score
    scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return scored_results


def _ensure_source_diversity(
    results: list[dict],
    top_k: int,
    max_per_source: int = 4,
) -> list[dict]:
    """
    Ensure diverse source representation in results.
    
    Prevents any single source from dominating the results,
    which improves claim extraction quality.
    """
    if not results:
        return []
    
    selected = []
    source_counts = {}
    
    for result in results:
        doc_id = result["document_id"]
        current_count = source_counts.get(doc_id, 0)
        
        # Allow up to max_per_source chunks per document
        if current_count < max_per_source:
            selected.append(result)
            source_counts[doc_id] = current_count + 1
        
        if len(selected) >= top_k:
            break
    
    # If we don't have enough, add remaining regardless of source
    if len(selected) < top_k:
        for result in results:
            if result not in selected:
                selected.append(result)
                if len(selected) >= top_k:
                    break
    
    return selected


@router.post("/expanded")
async def retrieve_with_expansion(
    request: RetrieveChunksRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> RetrieveChunksResponse:
    """
    Retrieve chunks with automatic query expansion.
    
    Generates multiple query variants and merges results
    for improved recall on complex research questions.
    """
    logger.info(f"Expanded retrieval for: {request.query[:100]}...")
    
    try:
        session_exists = await vector_store.session_exists(request.session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found."
            )
        
        # Generate query expansions
        queries = _expand_query(request.query)
        
        # Retrieve for each query variant
        all_results = {}  # Use dict to dedupe by chunk ID
        
        for query_variant in queries:
            results = await vector_store.search(
                session_id=request.session_id,
                query=query_variant,
                top_k=request.top_k,
                filters=request.filters,
            )
            
            for result in results:
                chunk_id = result["id"]
                if chunk_id not in all_results:
                    all_results[chunk_id] = result
                else:
                    # Keep higher score
                    if result["relevance_score"] > all_results[chunk_id]["relevance_score"]:
                        all_results[chunk_id] = result
        
        # Sort by relevance and take top_k
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["relevance_score"],
            reverse=True
        )[:request.top_k]
        
        chunks = [
            RetrievedChunk(
                id=r["id"],
                document_id=r["document_id"],
                source_title=r["source_title"],
                content=r["content"],
                relevance_score=r["relevance_score"],
                metadata=r.get("metadata", {}),
            )
            for r in sorted_results
        ]
        
        return RetrieveChunksResponse(
            success=True,
            query=request.query,
            chunks=chunks,
            total_results=len(chunks),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Expanded retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _expand_query(query: str) -> list[str]:
    """
    Generate query expansions for improved recall.
    
    Creates variants that may match different phrasings in documents.
    """
    queries = [query]  # Original query
    
    # Remove question words for keyword-focused search
    question_words = ["what", "how", "why", "when", "where", "which", "who", "is", "are", "does", "do"]
    words = query.lower().split()
    filtered_words = [w for w in words if w not in question_words and len(w) > 2]
    
    if filtered_words:
        keyword_query = " ".join(filtered_words)
        if keyword_query != query.lower():
            queries.append(keyword_query)
    
    # Extract noun phrases (simple heuristic)
    # Look for capitalized sequences or key terms
    key_terms = []
    for word in query.split():
        # Keep capitalized words (likely proper nouns or technical terms)
        if word[0].isupper() and len(word) > 2:
            key_terms.append(word)
    
    if key_terms:
        term_query = " ".join(key_terms)
        if term_query not in queries:
            queries.append(term_query)
    
    return queries[:3]  # Limit to 3 variants
