"""Research synthesis API routes.

POST /api/synthesize-report - Generate structured research brief from claims
"""

import time
from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    SynthesizeReportRequest,
    SynthesizeReportResponse,
    ResearchBrief,
)
from services.synthesizer import SynthesizerService
from services.vector_store import VectorStoreService

router = APIRouter(prefix="/synthesize-report", tags=["synthesis"])


def get_synthesizer() -> SynthesizerService:
    """Dependency to get synthesizer service."""
    return SynthesizerService()


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    return VectorStoreService()


@router.post("", response_model=SynthesizeReportResponse)
async def synthesize_report(
    request: SynthesizeReportRequest,
    synthesizer: SynthesizerService = Depends(get_synthesizer),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> SynthesizeReportResponse:
    """
    Synthesize a structured research brief from extracted claims.
    
    This endpoint:
    1. Retrieves extracted claims for the session
    2. Groups claims into consensus/disagreement/uncertain categories
    3. Identifies open research questions
    4. Generates limitations and confidence assessment
    5. Produces a structured research brief (NOT a chatbot response)
    
    Output follows strict JSON schema with:
    - Areas of consensus (supported by multiple sources)
    - Areas of disagreement (conflicting findings)
    - Open questions (under-explored areas)
    - Confidence level and limitations
    """
    start_time = time.time()
    
    try:
        # Verify session exists
        session_exists = await vector_store.session_exists(request.session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found. Process documents first."
            )
        
        # Get claims to synthesize
        if request.claim_ids:
            claims = await vector_store.get_claims_by_ids(
                request.session_id,
                request.claim_ids
            )
        else:
            claims = await vector_store.get_session_claims(request.session_id)
        
        if not claims:
            raise HTTPException(
                status_code=400,
                detail="No claims found. Extract claims first."
            )
        
        # Get source metadata
        sources = await vector_store.get_session_sources(request.session_id)
        
        # Synthesize research brief
        brief = await synthesizer.synthesize(
            session_id=request.session_id,
            query=request.query,
            claims=claims,
            sources=sources,
        )
        
        # Store the generated brief
        await vector_store.save_research_brief(request.session_id, brief)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return SynthesizeReportResponse(
            success=True,
            brief=brief,
            processing_time_ms=processing_time_ms,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis failed: {str(e)}"
        )
