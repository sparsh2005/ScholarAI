"""Research synthesis service.

Generates structured research briefs from extracted claims,
identifying consensus, disagreements, and open questions.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from openai import OpenAI

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


SYNTHESIS_PROMPT = """You are a research synthesizer creating a structured research brief.

Research Query: {query}

Sources Analyzed:
{sources}

Extracted Claims:
{claims}

Create a comprehensive research brief with:

1. CONSENSUS: Points where multiple sources agree (high confidence claims supported by 2+ sources)
2. DISAGREEMENTS: Points where sources conflict (identify both perspectives)
3. OPEN QUESTIONS: Areas needing more research (gaps, uncertainties, unexplored aspects)
4. LIMITATIONS: What this analysis cannot definitively answer

Output Format (JSON):
{{
  "consensus": [
    {{
      "statement": "Clear consensus statement",
      "confidence": 90,
      "source_count": 3,
      "evidence_summary": "Brief summary of supporting evidence"
    }}
  ],
  "disagreements": [
    {{
      "claim": "The contested claim",
      "perspective1": "View from some sources",
      "perspective2": "Opposing view from other sources",
      "source_count": 4
    }}
  ],
  "open_questions": [
    {{
      "question": "Important unanswered question",
      "context": "Why this question matters and what's known so far"
    }}
  ],
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "overall_confidence": "high|medium|low",
  "confidence_score": 75
}}

Generate the research brief:"""


class SynthesizerService:
    """Service for synthesizing research briefs from claims."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy-load OpenAI client."""
        if self._client is None:
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
        
        Args:
            session_id: Session identifier
            query: Original research query
            claims: Extracted and classified claims
            sources: Source metadata
            
        Returns:
            Complete ResearchBrief with consensus, disagreements, open questions
        """
        # Format inputs for prompt
        sources_text = self._format_sources(sources)
        claims_text = self._format_claims(claims)
        
        prompt = SYNTHESIS_PROMPT.format(
            query=query,
            sources=sources_text,
            claims=claims_text,
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You synthesize research findings into structured briefs. "
                            "Be analytical, not conversational. Output valid JSON only."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Build brief from LLM output
            return self._build_brief(
                session_id=session_id,
                query=query,
                sources=sources,
                claims=claims,
                synthesis=result,
            )
            
        except Exception as e:
            # Fall back to rule-based synthesis
            print(f"LLM synthesis error: {e}")
            return self._fallback_synthesis(
                session_id=session_id,
                query=query,
                sources=sources,
                claims=claims,
            )
    
    def _format_sources(self, sources: list[Source]) -> str:
        """Format sources for the prompt."""
        formatted = []
        for source in sources:
            authors = ", ".join(source.authors) if source.authors else "Unknown"
            formatted.append(
                f"- {source.title} ({source.date or 'n.d.'}) by {authors} "
                f"[{source.claims_extracted} claims extracted]"
            )
        return "\n".join(formatted)
    
    def _format_claims(self, claims: list[Claim]) -> str:
        """Format claims for the prompt."""
        formatted = []
        for claim in claims:
            type_label = claim.type.value.upper()
            formatted.append(
                f"[{type_label}] {claim.statement}\n"
                f"  Confidence: {claim.confidence}% | "
                f"Supporting: {claim.supporting_sources} | "
                f"Contradicting: {claim.contradicting_sources}"
            )
        return "\n\n".join(formatted)
    
    def _build_brief(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
        claims: list[Claim],
        synthesis: dict,
    ) -> ResearchBrief:
        """Build ResearchBrief from LLM synthesis output."""
        # Build consensus items
        consensus = [
            ConsensusItem(
                id=str(uuid.uuid4()),
                statement=item.get("statement", ""),
                confidence=item.get("confidence", 80),
                sources=item.get("source_count", 0),
                evidence_summary=item.get("evidence_summary"),
            )
            for item in synthesis.get("consensus", [])
        ]
        
        # Build disagreement items
        disagreements = [
            DisagreementItem(
                id=str(uuid.uuid4()),
                claim=item.get("claim", ""),
                perspective1=item.get("perspective1", ""),
                perspective2=item.get("perspective2", ""),
                sources=item.get("source_count", 0),
            )
            for item in synthesis.get("disagreements", [])
        ]
        
        # Build open questions
        open_questions = [
            OpenQuestion(
                id=str(uuid.uuid4()),
                question=item.get("question", ""),
                context=item.get("context", ""),
            )
            for item in synthesis.get("open_questions", [])
        ]
        
        # Determine confidence level
        confidence_str = synthesis.get("overall_confidence", "medium")
        confidence_level = ConfidenceLevel(confidence_str)
        confidence_score = synthesis.get("confidence_score", 70)
        
        limitations = synthesis.get("limitations", [])
        
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
    
    def _fallback_synthesis(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
        claims: list[Claim],
    ) -> ResearchBrief:
        """Rule-based fallback synthesis when LLM fails."""
        # Group claims by type
        consensus_claims = [c for c in claims if c.type == ClaimType.CONSENSUS]
        disagreement_claims = [c for c in claims if c.type == ClaimType.DISAGREEMENT]
        uncertain_claims = [c for c in claims if c.type == ClaimType.UNCERTAIN]
        
        # Build consensus from high-confidence consensus claims
        consensus = [
            ConsensusItem(
                id=str(uuid.uuid4()),
                statement=claim.statement,
                confidence=claim.confidence,
                sources=claim.supporting_sources,
                source_ids=claim.source_ids,
            )
            for claim in consensus_claims[:5]  # Top 5
        ]
        
        # Build disagreements
        disagreements = [
            DisagreementItem(
                id=str(uuid.uuid4()),
                claim=claim.statement,
                perspective1="Supported by some sources",
                perspective2="Contradicted by other sources",
                sources=claim.supporting_sources + claim.contradicting_sources,
                source_ids=claim.source_ids,
            )
            for claim in disagreement_claims[:3]
        ]
        
        # Build open questions from uncertain claims
        open_questions = [
            OpenQuestion(
                id=str(uuid.uuid4()),
                question=f"What is the evidence for: {claim.statement}?",
                context="This claim has limited or conflicting evidence in the analyzed sources.",
                related_claim_ids=[claim.id],
            )
            for claim in uncertain_claims[:3]
        ]
        
        # Calculate overall confidence
        if len(consensus_claims) > len(disagreement_claims):
            confidence_level = ConfidenceLevel.HIGH
            confidence_score = 80
        elif len(disagreement_claims) > len(consensus_claims):
            confidence_level = ConfidenceLevel.LOW
            confidence_score = 45
        else:
            confidence_level = ConfidenceLevel.MEDIUM
            confidence_score = 65
        
        limitations = [
            f"Based on {len(sources)} sources; comprehensive review may require more",
            "Automated extraction may miss nuanced arguments",
            "Confidence levels are approximations based on source agreement",
        ]
        
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
