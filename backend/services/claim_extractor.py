"""Claim extraction service using LLM.

Extracts normalized, structured claims from document chunks
and classifies them by agreement level across sources.
"""

import json
import uuid
from typing import Optional

from openai import OpenAI

from models.schemas import Claim, ClaimType, DocumentChunk, Source
from config import get_settings


CLAIM_EXTRACTION_PROMPT = """You are a research analyst extracting factual claims from academic sources.

Given the following document chunks related to the research query, extract distinct factual claims.

Research Query: {query}

Document Chunks:
{chunks}

Instructions:
1. Extract specific, verifiable claims from the text
2. Each claim should be a single, atomic statement
3. Include the source document ID for each claim
4. Assign a confidence score (0-100) based on how clearly the claim is stated
5. Note any qualifications or limitations mentioned

Output Format (JSON array):
[
  {{
    "statement": "Clear, atomic claim statement",
    "source_ids": ["doc_id_1", "doc_id_2"],
    "evidence": ["Direct quote or paraphrase supporting this claim"],
    "confidence": 85
  }}
]

Extract claims now:"""


CLAIM_CLASSIFICATION_PROMPT = """You are a research analyst classifying claims by agreement level.

Given these claims extracted from multiple sources, classify each claim:
- "consensus": Supported by multiple sources with no contradictions
- "disagreement": Sources present conflicting views on this topic
- "uncertain": Limited evidence or ambiguous support

Claims to classify:
{claims}

For each claim, determine:
1. Type (consensus/disagreement/uncertain)
2. Number of supporting sources
3. Number of contradicting sources
4. Confidence adjustment if needed

Output Format (JSON array):
[
  {{
    "claim_id": "original claim id",
    "type": "consensus|disagreement|uncertain",
    "supporting_sources": 3,
    "contradicting_sources": 0,
    "confidence": 90
  }}
]

Classify now:"""


class ClaimExtractorService:
    """Service for extracting and classifying claims using LLM."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy-load OpenAI client."""
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client
    
    async def extract_claims(
        self,
        query: str,
        chunks: list[DocumentChunk],
        sources: list[Source],
    ) -> list[Claim]:
        """
        Extract structured claims from document chunks.
        
        Args:
            query: Research query guiding extraction
            chunks: Document chunks to extract from
            sources: Source metadata for attribution
            
        Returns:
            List of extracted claims (not yet classified)
        """
        # Format chunks for prompt
        chunks_text = self._format_chunks(chunks)
        
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            query=query,
            chunks=chunks_text,
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You extract factual claims from research documents. Output valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Handle both direct array and wrapped object
            claims_data = result if isinstance(result, list) else result.get("claims", [])
            
            # Build source title lookup
            source_lookup = {s.id: s.title for s in sources}
            
            claims = []
            for i, claim_data in enumerate(claims_data):
                claim_id = str(uuid.uuid4())
                source_ids = claim_data.get("source_ids", [])
                
                claims.append(Claim(
                    id=claim_id,
                    statement=claim_data.get("statement", ""),
                    type=ClaimType.UNCERTAIN,  # Will be classified later
                    confidence=claim_data.get("confidence", 50),
                    supporting_sources=len(source_ids),
                    contradicting_sources=0,
                    source_ids=source_ids,
                    evidence=claim_data.get("evidence", []),
                    metadata={
                        "extraction_order": i,
                        "source_titles": [source_lookup.get(sid, "") for sid in source_ids],
                    },
                ))
            
            return claims
            
        except Exception as e:
            # Return empty list on error (will be logged)
            print(f"Claim extraction error: {e}")
            return []
    
    async def classify_claims(self, claims: list[Claim]) -> list[Claim]:
        """
        Classify claims by agreement level across sources.
        
        Args:
            claims: Claims to classify
            
        Returns:
            Claims with updated type and confidence
        """
        if not claims:
            return []
        
        # Format claims for classification
        claims_text = json.dumps([
            {
                "id": c.id,
                "statement": c.statement,
                "source_ids": c.source_ids,
                "initial_confidence": c.confidence,
            }
            for c in claims
        ], indent=2)
        
        prompt = CLAIM_CLASSIFICATION_PROMPT.format(claims=claims_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You classify research claims by agreement level. Output valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Handle both direct array and wrapped object
            classifications = result if isinstance(result, list) else result.get("classifications", [])
            
            # Build lookup
            classification_lookup = {c["claim_id"]: c for c in classifications}
            
            # Update claims
            for claim in claims:
                if claim.id in classification_lookup:
                    cls = classification_lookup[claim.id]
                    claim.type = ClaimType(cls.get("type", "uncertain"))
                    claim.supporting_sources = cls.get("supporting_sources", claim.supporting_sources)
                    claim.contradicting_sources = cls.get("contradicting_sources", 0)
                    claim.confidence = cls.get("confidence", claim.confidence)
                else:
                    # Default classification based on source count
                    claim.type = self._default_classification(claim)
            
            return claims
            
        except Exception as e:
            # Fall back to default classification
            print(f"Claim classification error: {e}")
            for claim in claims:
                claim.type = self._default_classification(claim)
            return claims
    
    def _format_chunks(self, chunks: list[DocumentChunk]) -> str:
        """Format chunks for the prompt."""
        formatted = []
        for chunk in chunks:
            source_title = chunk.metadata.get("source_title", "Unknown")
            formatted.append(
                f"[Source: {source_title} | Document ID: {chunk.document_id}]\n"
                f"{chunk.content}\n"
            )
        return "\n---\n".join(formatted)
    
    def _default_classification(self, claim: Claim) -> ClaimType:
        """Default classification based on source count."""
        if len(claim.source_ids) >= 3:
            return ClaimType.CONSENSUS
        elif len(claim.source_ids) == 1:
            return ClaimType.UNCERTAIN
        else:
            return ClaimType.UNCERTAIN
