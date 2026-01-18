"""ScholarAI Backend - FastAPI Application

An autonomous research engineer that synthesizes knowledge from arbitrary
documents using advanced RAG workflows powered by Docling.

API Endpoints:
- POST /api/process-docs    - Process documents via Docling
- POST /api/retrieve-chunks - Retrieve relevant chunks via vector search
- POST /api/extract-claims  - Extract structured claims from chunks
- POST /api/synthesize-report - Generate research brief from claims
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    documents_router,
    retrieval_router,
    claims_router,
    synthesis_router,
)
from config import get_settings, init_directories


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    init_directories()
    print("🧠 ScholarAI Backend starting...")
    print("📁 Data directories initialized")
    yield
    # Shutdown
    print("👋 ScholarAI Backend shutting down...")


# Create FastAPI application
app = FastAPI(
    title="ScholarAI API",
    description=(
        "Autonomous research engineer API. Ingests documents via Docling, "
        "synthesizes structured research insights using RAG, and produces "
        "organized briefs exposing agreement, disagreement, and open questions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(documents_router, prefix="/api")
app.include_router(retrieval_router, prefix="/api")
app.include_router(claims_router, prefix="/api")
app.include_router(synthesis_router, prefix="/api")


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "name": "ScholarAI API",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "process_docs": "POST /api/process-docs",
            "retrieve_chunks": "POST /api/retrieve-chunks",
            "extract_claims": "POST /api/extract-claims",
            "synthesize_report": "POST /api/synthesize-report",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
