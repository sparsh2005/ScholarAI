"""Claim extraction service using LLM.

Extracts normalized, structured claims from document chunks
and classifies them by agreement level across sources.

Pipeline:
1. Extract atomic claims from chunks
2. Deduplicate similar claims
3. Cluster semantically related claims
4. Classify by agreement level (consensus/disagreement/uncertain)
5. Validate output against strict schema
"""

import json
import uuid
import logging
from typing import Optional, Any
from collections import defaultdict

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from models.schemas import Claim, ClaimType, DocumentChunk, Source
from services.embedding_service import EmbeddingService
from config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Strict Output Schemas for LLM
# =============================================================================

class ExtractedClaimSchema(BaseModel):
    """Schema for a single extracted claim from LLM."""
    statement: str = Field(..., min_length=10, max_length=500, description="Clear, atomic claim statement")
    source_ids: list[str] = Field(..., min_length=1, description="Document IDs supporting this claim")
    evidence: list[str] = Field(default_factory=list, description="Direct quotes or paraphrases")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    scope: str = Field(default="general", description="Scope: general, specific, or qualified")


class ExtractionResponseSchema(BaseModel):
    """Schema for the complete extraction response."""
    claims: list[ExtractedClaimSchema]
    extraction_notes: str = Field(default="", description="Notes about extraction quality")


class ClassificationSchema(BaseModel):
    """Schema for claim classification result."""
    claim_id: str
    type: str = Field(..., pattern="^(consensus|disagreement|uncertain)$")
    supporting_sources: int = Field(..., ge=0)
    contradicting_sources: int = Field(..., ge=0)
    confidence: int = Field(..., ge=0, le=100)
    reasoning: str = Field(default="", description="Brief reasoning for classification")


class ClassificationResponseSchema(BaseModel):
    """Schema for complete classification response."""
    classifications: list[ClassificationSchema]


# =============================================================================
# Prompts
# =============================================================================

CLAIM_EXTRACTION_SYSTEM = """You are a precise research analyst extracting factual claims from academic sources.

Your task is to identify distinct, verifiable claims that directly address the research question.

Rules:
1. Each claim must be atomic (single idea, not compound)
2. Each claim must be specific and falsifiable
3. Avoid vague or opinion-based statements
4. Include only claims that appear in the provided text
5. Do not hallucinate or infer claims not present
6. Attribute each claim to its source document(s)

Output valid JSON matching the exact schema provided."""

CLAIM_EXTRACTION_PROMPT = """Research Query: {query}

Document Chunks to Analyze:
{chunks}

Extract all distinct factual claims that are relevant to the research query.

For each claim:
- statement: A clear, atomic claim (10-500 chars)
- source_ids: List of document IDs where this claim appears
- evidence: Direct quotes or close paraphrases supporting the claim
- confidence: How clearly is this stated? (0-100)
- scope: "general" (broad claim), "specific" (narrow/conditional), or "qualified" (with caveats)

Output JSON:
{{
  "claims": [
    {{
      "statement": "Clear factual claim",
      "source_ids": ["doc_id_1"],
      "evidence": ["Supporting quote from text"],
      "confidence": 85,
      "scope": "general"
    }}
  ],
  "extraction_notes": "Any observations about the extraction"
}}

Extract claims now:"""


CLAIM_CLASSIFICATION_SYSTEM = """You are a research analyst determining agreement levels across sources.

Classify each claim based on how sources relate to it:
- "consensus": Multiple sources agree, no contradictions
- "disagreement": Sources present conflicting views
- "uncertain": Limited evidence, ambiguous, or single source

Be precise and provide reasoning for each classification."""

CLAIM_CLASSIFICATION_PROMPT = """Claims to Classify:
{claims}

Source Information:
{sources}

For each claim, determine:
1. type: consensus, disagreement, or uncertain
2. supporting_sources: How many sources support this claim
3. contradicting_sources: How many sources contradict this claim
4. confidence: Adjusted confidence (0-100) based on source agreement
5. reasoning: Brief explanation of classification

Output JSON:
{{
  "classifications": [
    {{
      "claim_id": "claim-uuid",
      "type": "consensus",
      "supporting_sources": 3,
      "contradicting_sources": 0,
      "confidence": 90,
      "reasoning": "Three independent sources confirm this finding"
    }}
  ]
}}

Classify now:"""


# =============================================================================
# Service Implementation
# =============================================================================

class ClaimExtractorService:
    """Service for extracting and classifying claims using LLM.
    
    Implements a multi-stage pipeline:
    1. Extract raw claims from document chunks
    2. Validate against strict schema
    3. Deduplicate similar claims
    4. Cluster semantically related claims
    5. Classify by agreement level
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None
        self._embedding_service: Optional[EmbeddingService] = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy-load OpenAI client."""
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client
    
    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    async def extract_claims(
        self,
        query: str,
        chunks: list[DocumentChunk],
        sources: list[Source],
    ) -> list[Claim]:
        """
        Extract structured claims from document chunks.
        
        Pipeline:
        1. Format chunks for LLM
        2. Call LLM with strict extraction prompt
        3. Validate response against schema
        4. Deduplicate similar claims
        5. Return validated claims
        
        Args:
            query: Research query guiding extraction
            chunks: Document chunks to extract from
            sources: Source metadata for attribution
            
        Returns:
            List of extracted claims (not yet classified)
        """
        if not chunks:
            logger.warning("No chunks provided for claim extraction")
            return []
        
        logger.info(f"Extracting claims from {len(chunks)} chunks for query: {query[:100]}...")
        
        # Format chunks for prompt
        chunks_text = self._format_chunks_for_extraction(chunks)
        
        # Build source ID mapping
        source_lookup = {s.id: s for s in sources}
        valid_source_ids = set(source_lookup.keys())
        
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            query=query,
            chunks=chunks_text,
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": CLAIM_EXTRACTION_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent extraction
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            raw_result = json.loads(content)
            
            # Validate against schema
            try:
                validated = ExtractionResponseSchema(**raw_result)
                claims_data = validated.claims
                logger.info(f"Extracted {len(claims_data)} claims (validated)")
            except ValidationError as e:
                logger.warning(f"Schema validation failed, using raw data: {e}")
                claims_data = self._parse_raw_claims(raw_result)
            
            # Convert to Claim objects
            claims = []
            for i, claim_data in enumerate(claims_data):
                claim_id = str(uuid.uuid4())
                
                # Filter to valid source IDs
                source_ids = [
                    sid for sid in claim_data.source_ids
                    if sid in valid_source_ids
                ]
                
                # If no valid sources, try to infer from chunks
                if not source_ids and chunks:
                    # Use the document IDs from chunks that might contain this claim
                    source_ids = list(set(c.document_id for c in chunks[:3]))
                
                claims.append(Claim(
                    id=claim_id,
                    statement=claim_data.statement,
                    type=ClaimType.UNCERTAIN,  # Will be classified later
                    confidence=claim_data.confidence,
                    supporting_sources=len(source_ids),
                    contradicting_sources=0,
                    source_ids=source_ids,
                    evidence=claim_data.evidence if hasattr(claim_data, 'evidence') else [],
                    metadata={
                        "extraction_order": i,
                        "scope": claim_data.scope if hasattr(claim_data, 'scope') else "general",
                        "source_titles": [
                            source_lookup[sid].title 
                            for sid in source_ids 
                            if sid in source_lookup
                        ],
                    },
                ))
            
            # Deduplicate similar claims
            deduped_claims = await self._deduplicate_claims(claims)
            
            logger.info(f"Final claim count after deduplication: {len(deduped_claims)}")
            
            return deduped_claims
            
        except Exception as e:
            logger.error(f"Claim extraction error: {e}", exc_info=True)
            return []
    
    async def classify_claims(
        self,
        claims: list[Claim],
        sources: Optional[list[Source]] = None,
    ) -> list[Claim]:
        """
        Classify claims by agreement level across sources.
        
        Args:
            claims: Claims to classify
            sources: Optional source metadata for context
            
        Returns:
            Claims with updated type and confidence
        """
        if not claims:
            return []
        
        logger.info(f"Classifying {len(claims)} claims...")
        
        # Format claims for classification
        claims_text = json.dumps([
            {
                "id": c.id,
                "statement": c.statement,
                "source_ids": c.source_ids,
                "initial_confidence": c.confidence,
                "evidence_count": len(c.evidence),
            }
            for c in claims
        ], indent=2)
        
        # Format sources
        sources_text = "No source metadata available"
        if sources:
            sources_text = "\n".join([
                f"- {s.id}: {s.title} by {', '.join(s.authors) if s.authors else 'Unknown'}"
                for s in sources
            ])
        
        prompt = CLAIM_CLASSIFICATION_PROMPT.format(
            claims=claims_text,
            sources=sources_text,
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": CLAIM_CLASSIFICATION_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Very low for consistent classification
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            raw_result = json.loads(content)
            
            # Validate against schema
            try:
                validated = ClassificationResponseSchema(**raw_result)
                classifications = validated.classifications
            except ValidationError as e:
                logger.warning(f"Classification schema validation failed: {e}")
                classifications = self._parse_raw_classifications(raw_result)
            
            # Build lookup
            classification_lookup = {c.claim_id: c for c in classifications}
            
            # Update claims
            for claim in claims:
                if claim.id in classification_lookup:
                    cls = classification_lookup[claim.id]
                    
                    # Validate and set type
                    try:
                        claim.type = ClaimType(cls.type)
                    except ValueError:
                        claim.type = self._default_classification(claim)
                    
                    claim.supporting_sources = cls.supporting_sources
                    claim.contradicting_sources = cls.contradicting_sources
                    claim.confidence = cls.confidence
                    
                    # Store reasoning in metadata
                    if hasattr(cls, 'reasoning') and cls.reasoning:
                        claim.metadata["classification_reasoning"] = cls.reasoning
                else:
                    # Default classification
                    claim.type = self._default_classification(claim)
            
            logger.info(f"Classification complete: {self._count_by_type(claims)}")
            
            return claims
            
        except Exception as e:
            logger.error(f"Claim classification error: {e}", exc_info=True)
            # Fall back to rule-based classification
            for claim in claims:
                claim.type = self._default_classification(claim)
            return claims
    
    async def cluster_claims(
        self,
        claims: list[Claim],
        similarity_threshold: float = 0.75,
    ) -> dict[str, list[Claim]]:
        """
        Cluster semantically related claims.
        
        Uses embedding similarity to group related claims,
        useful for identifying themes and consolidating findings.
        
        Args:
            claims: Claims to cluster
            similarity_threshold: Minimum similarity for clustering (0-1)
            
        Returns:
            Dict mapping cluster IDs to lists of claims
        """
        if not claims or len(claims) < 2:
            return {"cluster_0": claims} if claims else {}
        
        logger.info(f"Clustering {len(claims)} claims...")
        
        # Get embeddings for all claim statements
        statements = [c.statement for c in claims]
        embeddings = self.embedding_service.embed_texts(statements)
        
        # Simple clustering using similarity threshold
        clusters: dict[str, list[Claim]] = {}
        claim_to_cluster: dict[str, str] = {}
        cluster_count = 0
        
        for i, claim in enumerate(claims):
            claim_embedding = embeddings[i]
            
            # Find most similar existing cluster
            best_cluster = None
            best_similarity = 0
            
            for cluster_id, cluster_claims in clusters.items():
                # Compare to first claim in cluster (representative)
                first_claim_idx = claims.index(cluster_claims[0])
                cluster_embedding = embeddings[first_claim_idx]
                
                similarity = self.embedding_service.compute_similarity(
                    claim_embedding, cluster_embedding
                )
                
                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_cluster = cluster_id
            
            if best_cluster:
                clusters[best_cluster].append(claim)
                claim_to_cluster[claim.id] = best_cluster
            else:
                # Create new cluster
                cluster_id = f"cluster_{cluster_count}"
                clusters[cluster_id] = [claim]
                claim_to_cluster[claim.id] = cluster_id
                cluster_count += 1
        
        logger.info(f"Created {len(clusters)} clusters from {len(claims)} claims")
        
        return clusters
    
    async def _deduplicate_claims(
        self,
        claims: list[Claim],
        similarity_threshold: float = 0.9,
    ) -> list[Claim]:
        """Remove near-duplicate claims based on semantic similarity."""
        if len(claims) <= 1:
            return claims
        
        # Get embeddings
        statements = [c.statement for c in claims]
        embeddings = self.embedding_service.embed_texts(statements)
        
        # Mark duplicates
        keep_indices = set(range(len(claims)))
        
        for i in range(len(claims)):
            if i not in keep_indices:
                continue
            for j in range(i + 1, len(claims)):
                if j not in keep_indices:
                    continue
                
                similarity = self.embedding_service.compute_similarity(
                    embeddings[i], embeddings[j]
                )
                
                if similarity >= similarity_threshold:
                    # Keep the one with higher confidence or more sources
                    if (claims[j].confidence > claims[i].confidence or
                        len(claims[j].source_ids) > len(claims[i].source_ids)):
                        keep_indices.discard(i)
                        # Merge source IDs
                        claims[j].source_ids = list(set(claims[j].source_ids + claims[i].source_ids))
                    else:
                        keep_indices.discard(j)
                        claims[i].source_ids = list(set(claims[i].source_ids + claims[j].source_ids))
        
        return [claims[i] for i in sorted(keep_indices)]
    
    def _format_chunks_for_extraction(self, chunks: list[DocumentChunk]) -> str:
        """Format chunks with clear source attribution."""
        formatted = []
        
        # Group by document
        by_doc: dict[str, list[DocumentChunk]] = defaultdict(list)
        for chunk in chunks:
            by_doc[chunk.document_id].append(chunk)
        
        for doc_id, doc_chunks in by_doc.items():
            source_title = doc_chunks[0].metadata.get("source_title", "Unknown")
            
            formatted.append(f"\n=== SOURCE: {source_title} (ID: {doc_id}) ===\n")
            
            for chunk in doc_chunks:
                section = chunk.metadata.get("section_title", "")
                if section:
                    formatted.append(f"\n[Section: {section}]")
                formatted.append(chunk.content)
            
            formatted.append("\n" + "=" * 50)
        
        return "\n".join(formatted)
    
    def _parse_raw_claims(self, raw_result: dict) -> list:
        """Parse claims from unvalidated LLM response."""
        claims = raw_result.get("claims", [])
        if not claims and isinstance(raw_result, list):
            claims = raw_result
        
        parsed = []
        for c in claims:
            try:
                parsed.append(ExtractedClaimSchema(
                    statement=c.get("statement", ""),
                    source_ids=c.get("source_ids", []),
                    evidence=c.get("evidence", []),
                    confidence=c.get("confidence", 50),
                    scope=c.get("scope", "general"),
                ))
            except Exception:
                continue
        
        return parsed
    
    def _parse_raw_classifications(self, raw_result: dict) -> list:
        """Parse classifications from unvalidated LLM response."""
        classifications = raw_result.get("classifications", [])
        if not classifications and isinstance(raw_result, list):
            classifications = raw_result
        
        parsed = []
        for c in classifications:
            try:
                parsed.append(ClassificationSchema(
                    claim_id=c.get("claim_id", ""),
                    type=c.get("type", "uncertain"),
                    supporting_sources=c.get("supporting_sources", 0),
                    contradicting_sources=c.get("contradicting_sources", 0),
                    confidence=c.get("confidence", 50),
                    reasoning=c.get("reasoning", ""),
                ))
            except Exception:
                continue
        
        return parsed
    
    def _default_classification(self, claim: Claim) -> ClaimType:
        """Rule-based default classification."""
        source_count = len(claim.source_ids)
        
        if source_count >= 3 and claim.confidence >= 70:
            return ClaimType.CONSENSUS
        elif source_count >= 2 and claim.confidence >= 60:
            return ClaimType.CONSENSUS
        elif claim.contradicting_sources > 0:
            return ClaimType.DISAGREEMENT
        else:
            return ClaimType.UNCERTAIN
    
    def _count_by_type(self, claims: list[Claim]) -> dict:
        """Count claims by type."""
        counts = {"consensus": 0, "disagreement": 0, "uncertain": 0}
        for claim in claims:
            counts[claim.type.value] += 1
        return counts
