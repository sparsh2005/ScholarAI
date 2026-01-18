"""Document processing API routes.

POST /api/process-docs - Process uploaded documents via Docling
POST /api/process-docs/upload - Upload a document for processing

This module handles the ingestion pipeline:
1. Accept file uploads or URLs
2. Process through Docling for structured extraction
3. Chunk content semantically
4. Embed and index in vector store
5. Return metadata and vector IDs
"""

import uuid
import time
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import Optional

from models.schemas import (
    ProcessDocsRequest,
    ProcessDocsResponse,
    Source,
    SourceStatus,
    ProcessedDocument,
)
from services.docling_service import DoclingService
from services.vector_store import VectorStoreService
from config import get_settings, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process-docs", tags=["documents"])

# Singleton instances for services (in production, use proper DI)
_docling_service: Optional[DoclingService] = None
_vector_store: Optional[VectorStoreService] = None


def get_docling_service() -> DoclingService:
    """Dependency to get Docling service (singleton)."""
    global _docling_service
    if _docling_service is None:
        _docling_service = DoclingService()
    return _docling_service


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service (singleton)."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


@router.post("", response_model=ProcessDocsResponse)
async def process_documents(
    request: ProcessDocsRequest,
    docling: DoclingService = Depends(get_docling_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> ProcessDocsResponse:
    """
    Process documents through the Docling pipeline and index them.
    
    This endpoint orchestrates the full document processing pipeline:
    
    1. **Document Retrieval**: Locates uploaded documents by ID
    2. **URL Fetching**: Downloads content from provided URLs
    3. **Docling Processing**: Converts all sources to structured Markdown/JSON
       - Extracts text, tables, and images
       - Preserves document structure
       - Extracts metadata (title, authors, date)
    4. **Chunking**: Splits content into semantic chunks
       - Respects section boundaries
       - Maintains sentence integrity
       - Applies overlap for context
    5. **Embedding**: Generates vector embeddings for each chunk
    6. **Indexing**: Stores chunks in ChromaDB vector store
    
    Request Body:
    ```json
    {
        "document_ids": ["uuid-1", "uuid-2"],
        "urls": ["https://example.com/paper.pdf"],
        "query": "Research question for context"
    }
    ```
    
    Returns:
        ProcessDocsResponse with session_id, sources, chunk counts, and any errors
    """
    start_time = time.time()
    session_id = str(uuid.uuid4())
    sources: list[Source] = []
    processed_docs: list[ProcessedDocument] = []
    errors: list[str] = []
    total_chunks = 0
    
    logger.info(f"Starting document processing for session {session_id}")
    logger.info(f"Documents: {len(request.document_ids)}, URLs: {len(request.urls)}")
    
    # Process uploaded documents
    for doc_id in request.document_ids:
        try:
            logger.info(f"Processing document: {doc_id}")
            
            # Process document through Docling
            processed = await docling.process_document(doc_id)
            
            if processed:
                processed_docs.append(processed)
                
                # Chunk the document
                chunks = await docling.chunk_document(processed)
                
                # Index chunks in vector store
                chunk_ids = await vector_store.index_chunks(session_id, chunks)
                total_chunks += len(chunks)
                
                # Create source entry with vector store IDs
                sources.append(Source(
                    id=processed.id,
                    title=processed.title,
                    authors=processed.authors,
                    date=processed.date,
                    type=processed.file_type,
                    status=SourceStatus.PROCESSED,
                    claims_extracted=0,  # Updated after claim extraction
                    relevance_score=0.0,  # Computed during retrieval
                    thumbnail_color=_generate_color(len(sources)),
                ))
                
                logger.info(f"Document {doc_id} processed: {len(chunks)} chunks indexed")
                
        except FileNotFoundError as e:
            error_msg = f"Document {doc_id} not found: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error processing document {doc_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    # Process URLs
    for url in request.urls:
        try:
            logger.info(f"Processing URL: {url}")
            
            processed = await docling.process_url(url)
            
            if processed:
                processed_docs.append(processed)
                
                # Chunk and index
                chunks = await docling.chunk_document(processed)
                chunk_ids = await vector_store.index_chunks(session_id, chunks)
                total_chunks += len(chunks)
                
                sources.append(Source(
                    id=processed.id,
                    title=processed.title,
                    authors=processed.authors,
                    date=processed.date,
                    type="url",
                    status=SourceStatus.PROCESSED,
                    claims_extracted=0,
                    relevance_score=0.0,
                    thumbnail_color=_generate_color(len(sources)),
                ))
                
                logger.info(f"URL processed: {len(chunks)} chunks indexed")
                
        except Exception as e:
            error_msg = f"Error processing URL {url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    # Store session metadata for later retrieval
    await vector_store.save_session_metadata(
        session_id=session_id,
        query=request.query,
        sources=sources,
        processed_docs=processed_docs,
    )
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Determine success (at least one source processed)
    success = len(sources) > 0
    
    logger.info(
        f"Session {session_id} complete: "
        f"{len(sources)} sources, {total_chunks} chunks, "
        f"{len(errors)} errors, {processing_time_ms}ms"
    )
    
    return ProcessDocsResponse(
        success=success,
        session_id=session_id,
        sources=sources,
        total_chunks=total_chunks,
        processing_time_ms=processing_time_ms,
        errors=errors,
    )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Upload a document for later processing.
    
    Accepts: PDF, DOCX, PPTX, PNG, JPG files up to 50MB.
    
    The uploaded file is stored temporarily and assigned a unique ID.
    Use this ID in the `/api/process-docs` endpoint to process the document.
    
    Supported formats:
    - **PDF** (application/pdf) - Research papers, reports
    - **DOCX** (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    - **PPTX** (application/vnd.openxmlformats-officedocument.presentationml.presentation)
    - **PNG** (image/png) - Screenshots, diagrams (OCR enabled)
    - **JPG/JPEG** (image/jpeg) - Photos, scanned documents (OCR enabled)
    
    Returns:
        ```json
        {
            "id": "uuid-string",
            "filename": "original_name.pdf",
            "file_type": "pdf",
            "file_size": 1234567,
            "upload_path": "data/uploads/uuid.pdf"
        }
        ```
    """
    # Validate file type
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
    }
    
    content_type = file.content_type or ""
    
    # Also check by file extension as fallback
    file_ext = Path(file.filename or "").suffix.lower().lstrip(".")
    ext_to_type = {"pdf": "pdf", "docx": "docx", "pptx": "pptx", "png": "png", "jpg": "jpg", "jpeg": "jpg"}
    
    if content_type not in allowed_types:
        if file_ext in ext_to_type:
            file_type = ext_to_type[file_ext]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type} ({file_ext}). Allowed: PDF, DOCX, PPTX, PNG, JPG"
            )
    else:
        file_type = allowed_types[content_type]
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(content) / 1024 / 1024:.1f}MB). Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Ensure upload directory exists
    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique ID and save file
    doc_id = str(uuid.uuid4())
    upload_path = upload_dir / f"{doc_id}.{file_type}"
    
    # Use aiofiles for async file writing
    import aiofiles
    async with aiofiles.open(upload_path, "wb") as f:
        await f.write(content)
    
    logger.info(f"Document uploaded: {file.filename} -> {upload_path} ({len(content)} bytes)")
    
    return {
        "id": doc_id,
        "filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "upload_path": str(upload_path),
    }


@router.get("/status/{session_id}")
async def get_processing_status(
    session_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> dict:
    """
    Get the processing status for a session.
    
    Returns current state, source counts, and any errors.
    """
    try:
        exists = await vector_store.session_exists(session_id)
        if not exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        sources = await vector_store.get_session_sources(session_id)
        chunks = await vector_store.get_session_chunks(session_id)
        
        return {
            "session_id": session_id,
            "status": "complete",
            "source_count": len(sources),
            "chunk_count": len(chunks),
            "sources": [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status,
                }
                for s in sources
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{session_id}")
async def get_session_sources(
    session_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> dict:
    """
    Get all processed sources for a session.
    
    Returns detailed metadata for each source including
    chunk counts and processing status.
    """
    try:
        exists = await vector_store.session_exists(session_id)
        if not exists:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        sources = await vector_store.get_session_sources(session_id)
        
        return {
            "session_id": session_id,
            "sources": [s.model_dump() if hasattr(s, 'model_dump') else s for s in sources],
            "total_sources": len(sources),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_color(index: int) -> str:
    """Generate a unique HSL color for source thumbnails.
    
    Uses a predefined palette of distinct, visually pleasing colors
    that cycle through for consistent but varied appearance.
    """
    hues = [
        0,    # Red
        210,  # Blue
        160,  # Teal
        280,  # Purple
        35,   # Orange
        120,  # Green
        300,  # Magenta
        180,  # Cyan
        45,   # Gold
        330,  # Pink
    ]
    hue = hues[index % len(hues)]
    saturation = 65 + (index % 3) * 10  # Vary saturation slightly
    lightness = 50 + (index % 2) * 10   # Vary lightness slightly
    return f"hsl({hue}, {saturation}%, {lightness}%)"
