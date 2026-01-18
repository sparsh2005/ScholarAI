"""Claim extraction API routes.

POST /api/extract-claims - Extract structured claims from retrieved chunks
"""

import time
from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    ExtractClaimsRequest,
    ExtractClaimsResponse,
    Claim,
    ClaimType,
)
from services.claim_extractor import ClaimExtractorService
from services.vector_store import VectorStoreService

router = APIRouter(prefix="/extract-claims", tags=["claims"])


def get_claim_extractor() -> ClaimExtractorService:
    """Dependency to get claim extractor service."""
    return ClaimExtractorService()


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    return VectorStoreService()


@router.post("", response_model=ExtractClaimsResponse)
async def extract_claims(
    request: ExtractClaimsRequest,
    extractor: ClaimExtractorService = Depends(get_claim_extractor),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> ExtractClaimsResponse:
    """
    Extract structured claims from document chunks.
    
    This endpoint:
    1. Retrieves indexed chunks (or uses specified chunk_ids)
    2. Sends chunks through LLM for claim extraction
    3. Normalizes claims into structured format
    4. Classifies claims by consensus level (agreement/disagreement/uncertain)
    5. Clusters related claims together
    
    Returns structured claims ready for synthesis.
    """
    try:
        # Verify session exists
        session_exists = await vector_store.session_exists(request.session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found. Process documents first."
            )
        
        # Get chunks to process
        if request.chunk_ids:
            chunks = await vector_store.get_chunks_by_ids(
                request.session_id, 
                request.chunk_ids
            )
        else:
            # Get all retrieved chunks for this session
            chunks = await vector_store.get_session_chunks(request.session_id)
        
        if not chunks:
            return ExtractClaimsResponse(
                success=True,
                query=request.query,
                claims=[],
                total_claims=0,
                consensus_count=0,
                disagreement_count=0,
                uncertain_count=0,
            )
        
        # Get source metadata for attribution
        sources = await vector_store.get_session_sources(request.session_id)
        
        # Extract claims using LLM
        claims = await extractor.extract_claims(
            query=request.query,
            chunks=chunks,
            sources=sources,
        )
        
        # Classify and cluster claims
        classified_claims = await extractor.classify_claims(claims)
        
        # Store claims in session
        await vector_store.save_session_claims(request.session_id, classified_claims)
        
        # Count by type
        consensus_count = sum(1 for c in classified_claims if c.type == ClaimType.CONSENSUS)
        disagreement_count = sum(1 for c in classified_claims if c.type == ClaimType.DISAGREEMENT)
        uncertain_count = sum(1 for c in classified_claims if c.type == ClaimType.UNCERTAIN)
        
        return ExtractClaimsResponse(
            success=True,
            query=request.query,
            claims=classified_claims,
            total_claims=len(classified_claims),
            consensus_count=consensus_count,
            disagreement_count=disagreement_count,
            uncertain_count=uncertain_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claim extraction failed: {str(e)}"
        )
