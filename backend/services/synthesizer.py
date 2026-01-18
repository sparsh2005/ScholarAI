"""Research synthesis service.

Generates structured research briefs from extracted claims,
identifying consensus, disagreements, and open questions.

This is NOT a chatbot - output is always structured JSON
following a strict schema for research workstation display.

Pipeline:
1. Group claims by type and theme
2. Generate synthesis via LLM
3. Validate against output schema
4. Compute confidence metrics
5. Return complete research brief
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Any
from collections import defaultdict

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator

from models.schemas import (
    Claim,
    ClaimType,
    Source,
    ResearchBrief,
    ConsensusItem,
    DisagreementItem,
    OpenQuestion,
    ConfidenceLevel,
)
from config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Strict Output Schemas
# =============================================================================

class ConsensusItemSchema(BaseModel):
    """Schema for consensus item in synthesis."""
    statement: str = Field(..., min_length=10, max_length=500)
    confidence: int = Field(..., ge=0, le=100)
    source_count: int = Field(..., ge=1)
    evidence_summary: str = Field(default="")
    related_claim_ids: list[str] = Field(default_factory=list)


class DisagreementItemSchema(BaseModel):
    """Schema for disagreement item in synthesis."""
    claim: str = Field(..., min_length=10, max_length=300)
    perspective1: str = Field(..., min_length=10, max_length=500)
    perspective2: str = Field(..., min_length=10, max_length=500)
    source_count: int = Field(..., ge=2)
    tension_level: str = Field(default="moderate", pattern="^(low|moderate|high)$")


class OpenQuestionSchema(BaseModel):
    """Schema for open question in synthesis."""
    question: str = Field(..., min_length=10, max_length=300)
    context: str = Field(..., min_length=10, max_length=500)
    importance: str = Field(default="medium", pattern="^(low|medium|high)$")


class SynthesisResponseSchema(BaseModel):
    """Complete schema for synthesis LLM response."""
    consensus: list[ConsensusItemSchema] = Field(default_factory=list)
    disagreements: list[DisagreementItemSchema] = Field(default_factory=list)
    open_questions: list[OpenQuestionSchema] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    overall_confidence: str = Field(default="medium", pattern="^(high|medium|low)$")
    confidence_score: int = Field(default=65, ge=0, le=100)
    key_insight: str = Field(default="", max_length=500)
    methodology_notes: str = Field(default="")
    
    @field_validator('limitations')
    @classmethod
    def validate_limitations(cls, v):
        return [lim[:200] for lim in v[:5]]  # Max 5 limitations, 200 chars each


# =============================================================================
# Prompts
# =============================================================================

SYNTHESIS_SYSTEM = """You are a research synthesis engine creating structured research briefs.

You are NOT a chatbot. Your output must be:
1. Strictly structured JSON
2. Analytical, not conversational
3. Based only on the provided claims and sources
4. Clear about confidence levels and limitations

Your goal is to help researchers understand:
- What sources agree on (consensus)
- Where sources conflict (disagreements)
- What remains unknown (open questions)
- How confident they should be in these findings"""

SYNTHESIS_PROMPT = """Research Query: {query}

## Sources Analyzed ({source_count} total)
{sources}

## Extracted Claims ({claim_count} total)
### Consensus Claims ({consensus_count}):
{consensus_claims}

### Disagreement Claims ({disagreement_count}):
{disagreement_claims}

### Uncertain Claims ({uncertain_count}):
{uncertain_claims}

## Task
Synthesize these findings into a structured research brief.

Requirements:
1. CONSENSUS: Identify 3-5 key points where sources agree
   - Only include claims with confidence ≥ 70% and 2+ supporting sources
   - Provide evidence summary for each

2. DISAGREEMENTS: Identify 2-3 areas where sources conflict
   - Clearly state both perspectives
   - Note the tension level (low/moderate/high)

3. OPEN QUESTIONS: Identify 2-4 important unanswered questions
   - Based on gaps in the evidence
   - Note importance (low/medium/high)

4. LIMITATIONS: List 3-5 limitations of this analysis

5. CONFIDENCE: Assess overall confidence
   - "high" if strong consensus, many sources, low disagreement
   - "medium" if mixed agreement or moderate source count
   - "low" if significant disagreement or limited sources
   - Provide numeric score 0-100

6. KEY INSIGHT: One sentence capturing the most important finding

Output strict JSON:
{{
  "consensus": [
    {{
      "statement": "Clear consensus statement",
      "confidence": 85,
      "source_count": 3,
      "evidence_summary": "Summary of supporting evidence",
      "related_claim_ids": []
    }}
  ],
  "disagreements": [
    {{
      "claim": "The contested topic",
      "perspective1": "View supported by some sources",
      "perspective2": "Opposing view from other sources",
      "source_count": 4,
      "tension_level": "moderate"
    }}
  ],
  "open_questions": [
    {{
      "question": "What remains unknown?",
      "context": "Why this matters and what we know so far",
      "importance": "high"
    }}
  ],
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "overall_confidence": "medium",
  "confidence_score": 72,
  "key_insight": "Most important finding in one sentence",
  "methodology_notes": "Notes about how synthesis was conducted"
}}

Generate the research brief now:"""


# =============================================================================
# Service Implementation
# =============================================================================

class SynthesizerService:
    """Service for synthesizing research briefs from claims.
    
    This service takes extracted and classified claims and produces
    a structured research brief suitable for display in a research
    workstation interface.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy-load OpenAI client."""
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client
    
    async def synthesize(
        self,
        session_id: str,
        query: str,
        claims: list[Claim],
        sources: list[Source],
    ) -> ResearchBrief:
        """
        Synthesize a structured research brief from claims.
        
        Pipeline:
        1. Group claims by classification
        2. Format context for LLM
        3. Generate synthesis
        4. Validate against schema
        5. Build ResearchBrief object
        
        Args:
            session_id: Session identifier
            query: Original research query
            claims: Extracted and classified claims
            sources: Source metadata
            
        Returns:
            Complete ResearchBrief with all sections
        """
        logger.info(f"Synthesizing brief for session {session_id}")
        logger.info(f"Query: {query[:100]}...")
        logger.info(f"Claims: {len(claims)}, Sources: {len(sources)}")
        
        if not claims:
            logger.warning("No claims provided for synthesis")
            return self._empty_brief(session_id, query, sources)
        
        # Group claims by type
        consensus_claims = [c for c in claims if c.type == ClaimType.CONSENSUS]
        disagreement_claims = [c for c in claims if c.type == ClaimType.DISAGREEMENT]
        uncertain_claims = [c for c in claims if c.type == ClaimType.UNCERTAIN]
        
        # Format for prompt
        sources_text = self._format_sources(sources)
        
        prompt = SYNTHESIS_PROMPT.format(
            query=query,
            source_count=len(sources),
            sources=sources_text,
            claim_count=len(claims),
            consensus_count=len(consensus_claims),
            consensus_claims=self._format_claims_by_type(consensus_claims),
            disagreement_count=len(disagreement_claims),
            disagreement_claims=self._format_claims_by_type(disagreement_claims),
            uncertain_count=len(uncertain_claims),
            uncertain_claims=self._format_claims_by_type(uncertain_claims),
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": SYNTHESIS_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            raw_result = json.loads(content)
            
            # Validate against schema
            try:
                validated = SynthesisResponseSchema(**raw_result)
                logger.info("Synthesis response validated successfully")
            except ValidationError as e:
                logger.warning(f"Schema validation failed, using partial data: {e}")
                validated = self._parse_partial_synthesis(raw_result)
            
            # Build final brief
            brief = self._build_brief(
                session_id=session_id,
                query=query,
                sources=sources,
                claims=claims,
                synthesis=validated,
            )
            
            logger.info(f"Brief generated: {len(brief.consensus)} consensus, "
                       f"{len(brief.disagreements)} disagreements, "
                       f"{len(brief.open_questions)} questions")
            
            return brief
            
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}", exc_info=True)
            return self._fallback_synthesis(
                session_id=session_id,
                query=query,
                sources=sources,
                claims=claims,
            )
    
    def _format_sources(self, sources: list[Source]) -> str:
        """Format sources for synthesis prompt."""
        if not sources:
            return "No source metadata available"
        
        formatted = []
        for i, source in enumerate(sources, 1):
            authors = ", ".join(source.authors[:3]) if source.authors else "Unknown"
            if len(source.authors) > 3:
                authors += f" et al."
            
            formatted.append(
                f"{i}. [{source.id[:8]}] {source.title}\n"
                f"   Authors: {authors} | Date: {source.date or 'n.d.'}\n"
                f"   Claims extracted: {source.claims_extracted}"
            )
        
        return "\n".join(formatted)
    
    def _format_claims_by_type(self, claims: list[Claim]) -> str:
        """Format claims for synthesis prompt."""
        if not claims:
            return "None"
        
        formatted = []
        for claim in claims:
            formatted.append(
                f"• [{claim.id[:8]}] {claim.statement}\n"
                f"  Confidence: {claim.confidence}% | "
                f"Sources: {claim.supporting_sources} supporting, "
                f"{claim.contradicting_sources} contradicting"
            )
        
        return "\n".join(formatted)
    
    def _build_brief(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
        claims: list[Claim],
        synthesis: SynthesisResponseSchema,
    ) -> ResearchBrief:
        """Build ResearchBrief from validated synthesis."""
        
        # Build consensus items
        consensus = []
        for item in synthesis.consensus:
            consensus.append(ConsensusItem(
                id=str(uuid.uuid4()),
                statement=item.statement,
                confidence=item.confidence,
                sources=item.source_count,
                source_ids=item.related_claim_ids,
                evidence_summary=item.evidence_summary or None,
            ))
        
        # Build disagreement items
        disagreements = []
        for item in synthesis.disagreements:
            disagreements.append(DisagreementItem(
                id=str(uuid.uuid4()),
                claim=item.claim,
                perspective1=item.perspective1,
                perspective2=item.perspective2,
                sources=item.source_count,
            ))
        
        # Build open questions
        open_questions = []
        for item in synthesis.open_questions:
            open_questions.append(OpenQuestion(
                id=str(uuid.uuid4()),
                question=item.question,
                context=item.context,
            ))
        
        # Determine confidence level
        try:
            confidence_level = ConfidenceLevel(synthesis.overall_confidence)
        except ValueError:
            confidence_level = ConfidenceLevel.MEDIUM
        
        # Add key insight to limitations if present
        limitations = list(synthesis.limitations)
        if synthesis.key_insight:
            # Store as first item in brief metadata
            pass
        
        return ResearchBrief(
            query=query,
            session_id=session_id,
            sources=sources,
            consensus=consensus,
            disagreements=disagreements,
            open_questions=open_questions,
            confidence_level=confidence_level,
            confidence_score=synthesis.confidence_score,
            limitations=limitations,
            generated_at=datetime.utcnow(),
        )
    
    def _parse_partial_synthesis(self, raw_result: dict) -> SynthesisResponseSchema:
        """Parse partial/invalid synthesis response."""
        return SynthesisResponseSchema(
            consensus=[
                ConsensusItemSchema(**c) for c in raw_result.get("consensus", [])
                if isinstance(c, dict) and c.get("statement")
            ][:5],
            disagreements=[
                DisagreementItemSchema(**d) for d in raw_result.get("disagreements", [])
                if isinstance(d, dict) and d.get("claim")
            ][:3],
            open_questions=[
                OpenQuestionSchema(**q) for q in raw_result.get("open_questions", [])
                if isinstance(q, dict) and q.get("question")
            ][:4],
            limitations=raw_result.get("limitations", [])[:5],
            overall_confidence=raw_result.get("overall_confidence", "medium"),
            confidence_score=raw_result.get("confidence_score", 65),
            key_insight=raw_result.get("key_insight", ""),
        )
    
    def _fallback_synthesis(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
        claims: list[Claim],
    ) -> ResearchBrief:
        """Rule-based fallback synthesis when LLM fails."""
        logger.info("Using fallback synthesis")
        
        # Group claims by type
        consensus_claims = [c for c in claims if c.type == ClaimType.CONSENSUS]
        disagreement_claims = [c for c in claims if c.type == ClaimType.DISAGREEMENT]
        uncertain_claims = [c for c in claims if c.type == ClaimType.UNCERTAIN]
        
        # Sort by confidence
        consensus_claims.sort(key=lambda c: c.confidence, reverse=True)
        disagreement_claims.sort(key=lambda c: c.confidence, reverse=True)
        
        # Build consensus from top claims
        consensus = [
            ConsensusItem(
                id=str(uuid.uuid4()),
                statement=claim.statement,
                confidence=claim.confidence,
                sources=claim.supporting_sources,
                source_ids=claim.source_ids,
                evidence_summary=claim.evidence[0] if claim.evidence else None,
            )
            for claim in consensus_claims[:5]
        ]
        
        # Build disagreements
        disagreements = [
            DisagreementItem(
                id=str(uuid.uuid4()),
                claim=claim.statement,
                perspective1="Supported by some sources in the analysis",
                perspective2="Contradicted or questioned by other sources",
                sources=claim.supporting_sources + claim.contradicting_sources,
                source_ids=claim.source_ids,
            )
            for claim in disagreement_claims[:3]
        ]
        
        # Build open questions from uncertain claims
        open_questions = [
            OpenQuestion(
                id=str(uuid.uuid4()),
                question=f"What is the evidence regarding: {claim.statement[:100]}?",
                context="This topic has limited or ambiguous evidence in the analyzed sources.",
                related_claim_ids=[claim.id],
            )
            for claim in uncertain_claims[:4]
        ]
        
        # Calculate confidence metrics
        total_claims = len(claims)
        consensus_ratio = len(consensus_claims) / total_claims if total_claims else 0
        disagreement_ratio = len(disagreement_claims) / total_claims if total_claims else 0
        
        if consensus_ratio > 0.6 and disagreement_ratio < 0.2:
            confidence_level = ConfidenceLevel.HIGH
            confidence_score = 80
        elif disagreement_ratio > 0.4:
            confidence_level = ConfidenceLevel.LOW
            confidence_score = 45
        else:
            confidence_level = ConfidenceLevel.MEDIUM
            confidence_score = 65
        
        # Adjust based on source count
        if len(sources) < 3:
            confidence_score = min(confidence_score, 60)
            confidence_level = ConfidenceLevel.MEDIUM if confidence_level == ConfidenceLevel.HIGH else confidence_level
        
        limitations = [
            f"Analysis based on {len(sources)} sources; additional sources may provide different perspectives",
            f"Extracted {len(claims)} claims through automated processing; manual review recommended",
            "Confidence levels are approximations based on source agreement patterns",
            "Some nuanced arguments may not be fully captured in atomic claims",
        ]
        
        if len(sources) < 5:
            limitations.append("Limited source coverage may affect comprehensiveness")
        
        return ResearchBrief(
            query=query,
            session_id=session_id,
            sources=sources,
            consensus=consensus,
            disagreements=disagreements,
            open_questions=open_questions,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            limitations=limitations,
            generated_at=datetime.utcnow(),
        )
    
    def _empty_brief(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
    ) -> ResearchBrief:
        """Generate empty brief when no claims available."""
        return ResearchBrief(
            query=query,
            session_id=session_id,
            sources=sources,
            consensus=[],
            disagreements=[],
            open_questions=[
                OpenQuestion(
                    id=str(uuid.uuid4()),
                    question="What evidence exists in the provided sources?",
                    context="No claims could be extracted from the documents. This may indicate the sources don't directly address the research question.",
                )
            ],
            confidence_level=ConfidenceLevel.LOW,
            confidence_score=20,
            limitations=[
                "No claims could be extracted from the provided sources",
                "The research question may not be addressed by these documents",
                "Try uploading more relevant sources or refining the query",
            ],
            generated_at=datetime.utcnow(),
        )
