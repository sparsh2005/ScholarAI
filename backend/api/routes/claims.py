"""Claim extraction API routes.

POST /api/extract-claims - Extract structured claims from retrieved chunks

This module implements the claim extraction stage:
1. Retrieve chunks for the session
2. Extract atomic claims using LLM
3. Deduplicate and cluster claims
4. Classify by agreement level
5. Validate against output schema
"""

import time
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    ExtractClaimsRequest,
    ExtractClaimsResponse,
    Claim,
    ClaimType,
)
from services.claim_extractor import ClaimExtractorService
from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract-claims", tags=["claims"])

# Singleton services
_claim_extractor: Optional[ClaimExtractorService] = None
_vector_store: Optional[VectorStoreService] = None


def get_claim_extractor() -> ClaimExtractorService:
    """Dependency to get claim extractor service."""
    global _claim_extractor
    if _claim_extractor is None:
        _claim_extractor = ClaimExtractorService()
    return _claim_extractor


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


@router.post("", response_model=ExtractClaimsResponse)
async def extract_claims(
    request: ExtractClaimsRequest,
    extractor: ClaimExtractorService = Depends(get_claim_extractor),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> ExtractClaimsResponse:
    """
    Extract structured claims from document chunks.
    
    This endpoint implements the claim extraction pipeline:
    
    1. **Chunk Retrieval**: Gets indexed chunks for the session
    2. **Claim Extraction**: LLM extracts atomic, verifiable claims
    3. **Deduplication**: Removes semantically similar claims
    4. **Classification**: Labels claims as consensus/disagreement/uncertain
    5. **Clustering**: Groups related claims (optional)
    6. **Validation**: Ensures output meets schema requirements
    
    The extracted claims are used for synthesis in the final pipeline step.
    
    Request Body:
    ```json
    {
        "session_id": "uuid",
        "query": "Research question",
        "chunk_ids": []  // Optional: specific chunks to use
    }
    ```
    
    Returns claims organized by type with confidence scores.
    """
    start_time = time.time()
    
    logger.info(f"Claim extraction request for session {request.session_id}")
    
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
            logger.info(f"Using {len(chunks)} specified chunks")
        else:
            # Get all chunks for this session
            chunks = await vector_store.get_session_chunks(request.session_id)
            logger.info(f"Using all {len(chunks)} session chunks")
        
        if not chunks:
            logger.warning("No chunks available for claim extraction")
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
        logger.info(f"Found {len(sources)} sources for attribution")
        
        # Stage 1: Extract claims using LLM
        claims = await extractor.extract_claims(
            query=request.query,
            chunks=chunks,
            sources=sources,
        )
        
        if not claims:
            logger.warning("No claims extracted")
            return ExtractClaimsResponse(
                success=True,
                query=request.query,
                claims=[],
                total_claims=0,
                consensus_count=0,
                disagreement_count=0,
                uncertain_count=0,
            )
        
        logger.info(f"Extracted {len(claims)} claims")
        
        # Stage 2: Classify claims by agreement level
        classified_claims = await extractor.classify_claims(claims, sources)
        
        # Stage 3: Optionally cluster claims (for large claim sets)
        if len(classified_claims) > 10:
            clusters = await extractor.cluster_claims(classified_claims)
            # Add cluster info to metadata
            for cluster_id, cluster_claims in clusters.items():
                for claim in cluster_claims:
                    claim.metadata["cluster_id"] = cluster_id
        
        # Store claims in session
        await vector_store.save_session_claims(request.session_id, classified_claims)
        
        # Update source claim counts
        source_claim_counts = _count_claims_per_source(classified_claims)
        for source in sources:
            if source.id in source_claim_counts:
                source.claims_extracted = source_claim_counts[source.id]
        await vector_store.save_session_metadata(
            request.session_id,
            request.query,
            sources,
        )
        
        # Count by type
        consensus_count = sum(1 for c in classified_claims if c.type == ClaimType.CONSENSUS)
        disagreement_count = sum(1 for c in classified_claims if c.type == ClaimType.DISAGREEMENT)
        uncertain_count = sum(1 for c in classified_claims if c.type == ClaimType.UNCERTAIN)
        
        processing_time = time.time() - start_time
        logger.info(
            f"Claim extraction complete in {processing_time:.2f}s: "
            f"{consensus_count} consensus, {disagreement_count} disagreement, "
            f"{uncertain_count} uncertain"
        )
        
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
        logger.error(f"Claim extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Claim extraction failed: {str(e)}"
        )


@router.get("/{session_id}")
async def get_session_claims(
    session_id: str,
    claim_type: Optional[str] = None,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> dict:
    """
    Get extracted claims for a session.
    
    Optionally filter by claim type (consensus, disagreement, uncertain).
    """
    try:
        session_exists = await vector_store.session_exists(session_id)
        if not session_exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        claims = await vector_store.get_session_claims(session_id)
        
        # Filter by type if specified
        if claim_type:
            try:
                filter_type = ClaimType(claim_type)
                claims = [c for c in claims if c.type == filter_type]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid claim type: {claim_type}. Use: consensus, disagreement, uncertain"
                )
        
        return {
            "session_id": session_id,
            "claims": [c.model_dump() if hasattr(c, 'model_dump') else dict(c) for c in claims],
            "total_claims": len(claims),
            "by_type": {
                "consensus": sum(1 for c in claims if c.type == ClaimType.CONSENSUS),
                "disagreement": sum(1 for c in claims if c.type == ClaimType.DISAGREEMENT),
                "uncertain": sum(1 for c in claims if c.type == ClaimType.UNCERTAIN),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/reclassify")
async def reclassify_claims(
    session_id: str,
    extractor: ClaimExtractorService = Depends(get_claim_extractor),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> dict:
    """
    Re-run classification on existing claims.
    
    Useful if classification logic has been updated or
    if you want to reprocess with different parameters.
    """
    try:
        session_exists = await vector_store.session_exists(session_id)
        if not session_exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        claims = await vector_store.get_session_claims(session_id)
        if not claims:
            raise HTTPException(status_code=400, detail="No claims to reclassify")
        
        sources = await vector_store.get_session_sources(session_id)
        
        # Reclassify
        reclassified = await extractor.classify_claims(claims, sources)
        
        # Save updated claims
        await vector_store.save_session_claims(session_id, reclassified)
        
        return {
            "session_id": session_id,
            "reclassified_count": len(reclassified),
            "by_type": {
                "consensus": sum(1 for c in reclassified if c.type == ClaimType.CONSENSUS),
                "disagreement": sum(1 for c in reclassified if c.type == ClaimType.DISAGREEMENT),
                "uncertain": sum(1 for c in reclassified if c.type == ClaimType.UNCERTAIN),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _count_claims_per_source(claims: list[Claim]) -> dict[str, int]:
    """Count how many claims reference each source."""
    counts: dict[str, int] = {}
    for claim in claims:
        for source_id in claim.source_ids:
            counts[source_id] = counts.get(source_id, 0) + 1
    return counts
