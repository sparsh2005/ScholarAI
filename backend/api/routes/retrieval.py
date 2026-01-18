"""Chunk retrieval API routes.

POST /api/retrieve-chunks - Retrieve relevant chunks via vector search
"""

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    RetrieveChunksRequest,
    RetrieveChunksResponse,
    RetrievedChunk,
)
from services.vector_store import VectorStoreService

router = APIRouter(prefix="/retrieve-chunks", tags=["retrieval"])


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    return VectorStoreService()


@router.post("", response_model=RetrieveChunksResponse)
async def retrieve_chunks(
    request: RetrieveChunksRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> RetrieveChunksResponse:
    """
    Retrieve relevant document chunks using semantic search.
    
    This endpoint:
    1. Embeds the query using the same model as document indexing
    2. Performs vector similarity search in ChromaDB
    3. Returns top-k most relevant chunks with metadata
    
    The chunks are used for claim extraction in the next pipeline step.
    """
    try:
        # Verify session exists
        session_exists = await vector_store.session_exists(request.session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found. Process documents first."
            )
        
        # Retrieve chunks via semantic search
        results = await vector_store.search(
            session_id=request.session_id,
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
        )
        
        # Transform to response format
        chunks = [
            RetrievedChunk(
                id=r["id"],
                document_id=r["document_id"],
                source_title=r["source_title"],
                content=r["content"],
                relevance_score=r["relevance_score"],
                metadata=r.get("metadata", {}),
            )
            for r in results
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
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )
