"""ScholarAI Backend - FastAPI Application

An autonomous research engineer that synthesizes knowledge from arbitrary
documents using advanced RAG workflows powered by Docling.

API Endpoints:
- POST /api/process-docs       - Process documents via Docling
- POST /api/process-docs/upload - Upload a document file
- POST /api/retrieve-chunks    - Retrieve relevant chunks via vector search
- POST /api/extract-claims     - Extract structured claims from chunks
- POST /api/synthesize-report  - Generate research brief from claims
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    documents_router,
    retrieval_router,
    claims_router,
    synthesis_router,
)
from config import get_settings, init_directories


# Configure logging
def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    return logging.getLogger("scholarai")


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("🧠 ScholarAI Backend starting...")
    logger.info("=" * 60)
    
    # Initialize directories
    init_directories()
    settings = get_settings()
    
    logger.info(f"📁 Upload directory: {settings.upload_directory}")
    logger.info(f"📁 Processed directory: {settings.processed_directory}")
    logger.info(f"📁 ChromaDB directory: {settings.chroma_persist_directory}")
    logger.info(f"🤖 Embedding model: {settings.embedding_model}")
    logger.info(f"🧠 LLM model: {settings.openai_model}")
    
    # Check OpenAI API key
    if not settings.openai_api_key:
        logger.warning("⚠️  OPENAI_API_KEY not set - claim extraction and synthesis will fail")
    else:
        logger.info("✅ OpenAI API key configured")
    
    logger.info("-" * 60)
    logger.info("🚀 Server ready at http://localhost:8000")
    logger.info("📚 API docs at http://localhost:8000/docs")
    logger.info("-" * 60)
    
    yield
    
    # Shutdown
    logger.info("👋 ScholarAI Backend shutting down...")


# Create FastAPI application
app = FastAPI(
    title="ScholarAI API",
    description="""
## Autonomous Research Engineer API

ScholarAI ingests documents via Docling, synthesizes structured research insights 
using RAG, and produces organized briefs exposing agreement, disagreement, and open questions.

### Pipeline Stages

1. **Document Processing** (`/api/process-docs`)
   - Upload PDF, DOCX, PPTX, or images
   - Docling extracts structured content
   - Content is chunked and embedded

2. **Retrieval** (`/api/retrieve-chunks`)
   - Semantic search over document chunks
   - Returns relevant passages for query

3. **Claim Extraction** (`/api/extract-claims`)
   - LLM extracts factual claims
   - Claims are classified by agreement level

4. **Synthesis** (`/api/synthesize-report`)
   - Generate structured research brief
   - Identifies consensus, disagreements, open questions

### This is NOT a chatbot
Output is always structured JSON, not conversational responses.
    """,
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
        "description": "Autonomous research engineer API",
        "endpoints": {
            "upload": "POST /api/process-docs/upload",
            "process_docs": "POST /api/process-docs",
            "retrieve_chunks": "POST /api/retrieve-chunks",
            "extract_claims": "POST /api/extract-claims",
            "synthesize_report": "POST /api/synthesize-report",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "scholarai-backend",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
