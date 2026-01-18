"""Data models and schemas for ScholarAI."""

from .schemas import (
    # Document models
    DocumentUpload,
    ProcessedDocument,
    DocumentChunk,
    ProcessDocsRequest,
    ProcessDocsResponse,
    
    # Retrieval models
    RetrieveChunksRequest,
    RetrieveChunksResponse,
    RetrievedChunk,
    
    # Claim models
    Claim,
    ClaimType,
    ExtractClaimsRequest,
    ExtractClaimsResponse,
    
    # Synthesis models
    ConsensusItem,
    DisagreementItem,
    OpenQuestion,
    ResearchBrief,
    SynthesizeReportRequest,
    SynthesizeReportResponse,
    
    # Source models
    Source,
    SourceStatus,
)

__all__ = [
    "DocumentUpload",
    "ProcessedDocument",
    "DocumentChunk",
    "ProcessDocsRequest",
    "ProcessDocsResponse",
    "RetrieveChunksRequest",
    "RetrieveChunksResponse",
    "RetrievedChunk",
    "Claim",
    "ClaimType",
    "ExtractClaimsRequest",
    "ExtractClaimsResponse",
    "ConsensusItem",
    "DisagreementItem",
    "OpenQuestion",
    "ResearchBrief",
    "SynthesizeReportRequest",
    "SynthesizeReportResponse",
    "Source",
    "SourceStatus",
]
