"""API route modules."""

from .documents import router as documents_router
from .retrieval import router as retrieval_router
from .claims import router as claims_router
from .synthesis import router as synthesis_router

__all__ = [
    "documents_router",
    "retrieval_router",
    "claims_router",
    "synthesis_router",
]
