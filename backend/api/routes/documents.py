"""Document processing API routes.

POST /api/process-docs - Process uploaded documents via Docling
"""

import uuid
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional

from models.schemas import (
    ProcessDocsRequest,
    ProcessDocsResponse,
    Source,
    SourceStatus,
)
from services.docling_service import DoclingService
from services.vector_store import VectorStoreService
from config import get_settings, Settings

router = APIRouter(prefix="/process-docs", tags=["documents"])


def get_docling_service() -> DoclingService:
    """Dependency to get Docling service."""
    return DoclingService()


def get_vector_store() -> VectorStoreService:
    """Dependency to get vector store service."""
    return VectorStoreService()


@router.post("", response_model=ProcessDocsResponse)
async def process_documents(
    request: ProcessDocsRequest,
    docling: DoclingService = Depends(get_docling_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> ProcessDocsResponse:
    """
    Process documents through the Docling pipeline and index them.
    
    This endpoint:
    1. Retrieves uploaded documents by ID
    2. Fetches content from provided URLs
    3. Processes all sources through Docling for structured extraction
    4. Chunks the content and stores embeddings in the vector store
    
    Returns processing results and source metadata.
    """
    start_time = time.time()
    session_id = str(uuid.uuid4())
    sources: list[Source] = []
    errors: list[str] = []
    total_chunks = 0
    
    # Process uploaded documents
    for doc_id in request.document_ids:
        try:
            # Process document through Docling
            processed = await docling.process_document(doc_id)
            
            if processed:
                # Chunk and index the document
                chunks = await docling.chunk_document(processed)
                await vector_store.index_chunks(session_id, chunks)
                total_chunks += len(chunks)
                
                # Create source entry
                sources.append(Source(
                    id=processed.id,
                    title=processed.title,
                    authors=processed.authors,
                    date=processed.date,
                    type=processed.file_type,
                    status=SourceStatus.PROCESSED,
                    claims_extracted=0,  # Will be updated after claim extraction
                    relevance_score=0.0,  # Will be computed during retrieval
                    thumbnail_color=_generate_color(len(sources)),
                ))
        except Exception as e:
            errors.append(f"Error processing document {doc_id}: {str(e)}")
    
    # Process URLs
    for url in request.urls:
        try:
            processed = await docling.process_url(url)
            
            if processed:
                chunks = await docling.chunk_document(processed)
                await vector_store.index_chunks(session_id, chunks)
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
        except Exception as e:
            errors.append(f"Error processing URL {url}: {str(e)}")
    
    # Store session metadata
    await vector_store.save_session_metadata(
        session_id=session_id,
        query=request.query,
        sources=sources,
    )
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    return ProcessDocsResponse(
        success=len(errors) == 0,
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
    Returns: Document ID for use in process-docs endpoint.
    """
    # Validate file type
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
        "image/png": "png",
        "image/jpeg": "jpg",
    }
    
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOCX, PPTX, PNG, JPG"
        )
    
    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Save file and return ID
    doc_id = str(uuid.uuid4())
    file_type = allowed_types[content_type]
    
    import aiofiles
    from pathlib import Path
    
    upload_path = Path(settings.upload_directory) / f"{doc_id}.{file_type}"
    async with aiofiles.open(upload_path, "wb") as f:
        await f.write(content)
    
    return {
        "id": doc_id,
        "filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
    }


def _generate_color(index: int) -> str:
    """Generate a unique HSL color for source thumbnails."""
    hues = [0, 210, 160, 280, 35, 120, 300, 180]
    hue = hues[index % len(hues)]
    return f"hsl({hue}, 70%, 55%)"
