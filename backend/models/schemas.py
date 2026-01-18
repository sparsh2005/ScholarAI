"""Pydantic schemas for ScholarAI API contracts.

These schemas define strict JSON contracts between frontend and backend,
ensuring type safety and validation across the research pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class SourceStatus(str, Enum):
    """Processing status of a source document."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class ClaimType(str, Enum):
    """Classification of claim based on source agreement."""
    CONSENSUS = "consensus"
    DISAGREEMENT = "disagreement"
    UNCERTAIN = "uncertain"


class ConfidenceLevel(str, Enum):
    """Overall confidence level for research brief."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# Document Models
# =============================================================================

class DocumentUpload(BaseModel):
    """Represents an uploaded document before processing."""
    id: str
    filename: str
    file_type: str  # pdf, docx, pptx, png, jpg
    file_size: int  # bytes
    upload_time: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """A processed chunk of document content."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[list[float]] = None


class ProcessedDocument(BaseModel):
    """A document after Docling processing."""
    id: str
    filename: str
    title: str
    authors: list[str] = Field(default_factory=list)
    date: Optional[str] = None
    file_type: str
    status: SourceStatus = SourceStatus.PENDING
    chunk_count: int = 0
    content_preview: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    processed_at: Optional[datetime] = None


class Source(BaseModel):
    """A research source with processing status and metrics."""
    id: str
    title: str
    authors: list[str]
    date: Optional[str] = None
    type: str  # pdf, docx, url, etc.
    status: SourceStatus
    claims_extracted: int = 0
    relevance_score: float = 0.0
    thumbnail_color: str = "hsl(210, 70%, 55%)"


# =============================================================================
# Process Documents API
# =============================================================================

class ProcessDocsRequest(BaseModel):
    """Request to process uploaded documents."""
    document_ids: list[str] = Field(
        ...,
        description="IDs of uploaded documents to process"
    )
    urls: list[str] = Field(
        default_factory=list,
        description="URLs to fetch and process"
    )
    query: str = Field(
        ...,
        description="Research query to guide processing"
    )


class ProcessDocsResponse(BaseModel):
    """Response after document processing."""
    success: bool
    session_id: str
    sources: list[Source]
    total_chunks: int
    processing_time_ms: int
    errors: list[str] = Field(default_factory=list)


# =============================================================================
# Retrieve Chunks API
# =============================================================================

class RetrievedChunk(BaseModel):
    """A chunk retrieved from vector search."""
    id: str
    document_id: str
    source_title: str
    content: str
    relevance_score: float
    metadata: dict = Field(default_factory=dict)


class RetrieveChunksRequest(BaseModel):
    """Request to retrieve relevant chunks."""
    session_id: str
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    filters: dict = Field(default_factory=dict)


class RetrieveChunksResponse(BaseModel):
    """Response with retrieved chunks."""
    success: bool
    query: str
    chunks: list[RetrievedChunk]
    total_results: int


# =============================================================================
# Extract Claims API
# =============================================================================

class Claim(BaseModel):
    """An extracted claim from research sources."""
    id: str
    statement: str
    type: ClaimType
    confidence: int = Field(..., ge=0, le=100)
    supporting_sources: int
    contradicting_sources: int
    source_ids: list[str]
    evidence: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ExtractClaimsRequest(BaseModel):
    """Request to extract claims from retrieved chunks."""
    session_id: str
    query: str
    chunk_ids: list[str] = Field(
        default_factory=list,
        description="Specific chunks to extract from (empty = use all retrieved)"
    )


class ExtractClaimsResponse(BaseModel):
    """Response with extracted claims."""
    success: bool
    query: str
    claims: list[Claim]
    total_claims: int
    consensus_count: int
    disagreement_count: int
    uncertain_count: int


# =============================================================================
# Synthesize Report API
# =============================================================================

class ConsensusItem(BaseModel):
    """A point of consensus across sources."""
    id: str
    statement: str
    confidence: int = Field(..., ge=0, le=100)
    sources: int
    source_ids: list[str] = Field(default_factory=list)
    evidence_summary: Optional[str] = None


class DisagreementItem(BaseModel):
    """A point of disagreement between sources."""
    id: str
    claim: str
    perspective1: str
    perspective2: str
    sources: int
    source_ids: list[str] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    """An open research question identified from sources."""
    id: str
    question: str
    context: str
    related_claim_ids: list[str] = Field(default_factory=list)


class ResearchBrief(BaseModel):
    """Complete structured research brief."""
    query: str
    session_id: str
    sources: list[Source]
    consensus: list[ConsensusItem]
    disagreements: list[DisagreementItem]
    open_questions: list[OpenQuestion]
    confidence_level: ConfidenceLevel
    confidence_score: int = Field(..., ge=0, le=100)
    limitations: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SynthesizeReportRequest(BaseModel):
    """Request to synthesize a research brief."""
    session_id: str
    query: str
    claim_ids: list[str] = Field(
        default_factory=list,
        description="Specific claims to synthesize (empty = use all)"
    )


class SynthesizeReportResponse(BaseModel):
    """Response with synthesized research brief."""
    success: bool
    brief: ResearchBrief
    processing_time_ms: int
