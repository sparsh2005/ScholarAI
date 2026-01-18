"""Research synthesis API routes.

POST /api/synthesize-report - Generate structured research brief from claims

This module implements the synthesis stage:
1. Retrieve extracted claims
2. Group by consensus/disagreement/uncertain
3. Generate structured brief via LLM
4. Validate against output schema
5. Return complete research brief
"""

import time
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import (
    SynthesizeReportRequest,
    SynthesizeReportResponse,
    ResearchBrief,
)
from services.synthesizer import SynthesizerService
from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/synthesize-report", tags=["synthesis"])

# Singleton services
_synthesizer: Optional[SynthesizerService] = None
_vector_store: Optional[VectorStoreService] = None


def get_synthesizer() -> SynthesizerService:
    """Dependency to get synthesizer service."""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = SynthesizerService()
    return _synthesizer


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


@router.post("", response_model=SynthesizeReportResponse)
async def synthesize_report(
    request: SynthesizeReportRequest,
    synthesizer: SynthesizerService = Depends(get_synthesizer),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> SynthesizeReportResponse:
    """
    Synthesize a structured research brief from extracted claims.
    
    This endpoint produces the final output of the ScholarAI pipeline:
    a structured research brief that is NOT a chatbot response.
    
    The brief contains:
    - **Consensus**: Points where multiple sources agree
    - **Disagreements**: Points where sources conflict (with both perspectives)
    - **Open Questions**: Areas needing more research
    - **Confidence Level**: Overall confidence assessment
    - **Limitations**: What the analysis cannot definitively answer
    
    Request Body:
    ```json
    {
        "session_id": "uuid",
        "query": "Research question",
        "claim_ids": []  // Optional: specific claims to synthesize
    }
    ```
    
    Returns:
    ```json
    {
        "success": true,
        "brief": {
            "query": "...",
            "sources": [...],
            "consensus": [...],
            "disagreements": [...],
            "open_questions": [...],
            "confidence_level": "high|medium|low",
            "confidence_score": 75,
            "limitations": [...]
        },
        "processing_time_ms": 1234
    }
    ```
    """
    start_time = time.time()
    
    logger.info(f"Synthesis request for session {request.session_id}")
    
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
            logger.info(f"Synthesizing from {len(claims)} specified claims")
        else:
            claims = await vector_store.get_session_claims(request.session_id)
            logger.info(f"Synthesizing from all {len(claims)} session claims")
        
        if not claims:
            logger.warning("No claims found for synthesis")
            raise HTTPException(
                status_code=400,
                detail="No claims found. Run claim extraction first with /api/extract-claims"
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
        
        logger.info(f"Synthesis complete in {processing_time_ms}ms")
        
        return SynthesizeReportResponse(
            success=True,
            brief=brief,
            processing_time_ms=processing_time_ms,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis failed: {str(e)}"
        )


@router.get("/{session_id}")
async def get_research_brief(
    session_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> dict:
    """
    Get the generated research brief for a session.
    
    Returns the previously generated brief without re-running synthesis.
    """
    try:
        session_exists = await vector_store.session_exists(session_id)
        if not session_exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        brief = await vector_store.get_research_brief(session_id)
        
        if not brief:
            raise HTTPException(
                status_code=404,
                detail="No research brief found. Run synthesis first with POST /api/synthesize-report"
            )
        
        return {
            "session_id": session_id,
            "brief": brief.model_dump() if hasattr(brief, 'model_dump') else dict(brief),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/export")
async def export_brief(
    session_id: str,
    format: str = "json",
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> JSONResponse:
    """
    Export the research brief in various formats.
    
    Supported formats:
    - json (default): Full structured JSON
    - markdown: Human-readable markdown
    - summary: Condensed summary
    """
    try:
        session_exists = await vector_store.session_exists(session_id)
        if not session_exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        brief = await vector_store.get_research_brief(session_id)
        
        if not brief:
            raise HTTPException(status_code=404, detail="No research brief found")
        
        if format == "json":
            return JSONResponse(
                content=brief.model_dump() if hasattr(brief, 'model_dump') else dict(brief),
                media_type="application/json",
            )
        
        elif format == "markdown":
            markdown = _brief_to_markdown(brief)
            return JSONResponse(
                content={"markdown": markdown},
                media_type="application/json",
            )
        
        elif format == "summary":
            summary = _brief_to_summary(brief)
            return JSONResponse(
                content={"summary": summary},
                media_type="application/json",
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown format: {format}. Supported: json, markdown, summary"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _brief_to_markdown(brief: ResearchBrief) -> str:
    """Convert research brief to markdown format."""
    lines = [
        f"# Research Brief",
        f"",
        f"**Query:** {brief.query}",
        f"",
        f"**Confidence:** {brief.confidence_level.value.upper()} ({brief.confidence_score}%)",
        f"",
        f"**Sources Analyzed:** {len(brief.sources)}",
        f"",
    ]
    
    # Consensus
    if brief.consensus:
        lines.append("## Areas of Consensus")
        lines.append("")
        for i, item in enumerate(brief.consensus, 1):
            lines.append(f"{i}. **{item.statement}**")
            lines.append(f"   - Confidence: {item.confidence}%")
            lines.append(f"   - Supported by {item.sources} sources")
            if item.evidence_summary:
                lines.append(f"   - Evidence: {item.evidence_summary}")
            lines.append("")
    
    # Disagreements
    if brief.disagreements:
        lines.append("## Areas of Disagreement")
        lines.append("")
        for i, item in enumerate(brief.disagreements, 1):
            lines.append(f"### {i}. {item.claim}")
            lines.append("")
            lines.append(f"**Supporting view:** {item.perspective1}")
            lines.append("")
            lines.append(f"**Opposing view:** {item.perspective2}")
            lines.append("")
            lines.append(f"*Based on {item.sources} sources*")
            lines.append("")
    
    # Open Questions
    if brief.open_questions:
        lines.append("## Open Questions")
        lines.append("")
        for i, item in enumerate(brief.open_questions, 1):
            lines.append(f"{i}. **{item.question}**")
            lines.append(f"   - {item.context}")
            lines.append("")
    
    # Limitations
    if brief.limitations:
        lines.append("## Limitations")
        lines.append("")
        for limitation in brief.limitations:
            lines.append(f"- {limitation}")
        lines.append("")
    
    # Sources
    lines.append("## Sources")
    lines.append("")
    for source in brief.sources:
        authors = ", ".join(source.authors[:3]) if source.authors else "Unknown"
        lines.append(f"- {source.title} ({source.date or 'n.d.'}) - {authors}")
    
    return "\n".join(lines)


def _brief_to_summary(brief: ResearchBrief) -> str:
    """Generate a condensed summary of the brief."""
    parts = [
        f"Research Question: {brief.query}",
        "",
        f"Overall Confidence: {brief.confidence_level.value.upper()} ({brief.confidence_score}%)",
        f"Sources: {len(brief.sources)}",
        "",
    ]
    
    if brief.consensus:
        parts.append(f"Key Findings ({len(brief.consensus)} consensus points):")
        for item in brief.consensus[:3]:
            parts.append(f"• {item.statement}")
        parts.append("")
    
    if brief.disagreements:
        parts.append(f"Contested Points ({len(brief.disagreements)}):")
        for item in brief.disagreements[:2]:
            parts.append(f"• {item.claim}")
        parts.append("")
    
    if brief.open_questions:
        parts.append(f"Open Questions ({len(brief.open_questions)}):")
        for item in brief.open_questions[:2]:
            parts.append(f"• {item.question}")
    
    return "\n".join(parts)
