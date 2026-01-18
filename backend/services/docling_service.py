"""Docling document processing service.

Handles conversion of arbitrary documents (PDF, DOCX, PPTX, images)
into structured, RAG-ready content using Docling.
"""

import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from models.schemas import ProcessedDocument, DocumentChunk, SourceStatus
from config import get_settings


class DoclingService:
    """Service for document processing via Docling."""
    
    def __init__(self):
        self.settings = get_settings()
        self._converter = None
    
    @property
    def converter(self):
        """Lazy-load Docling converter."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter
            self._converter = DocumentConverter()
        return self._converter
    
    async def process_document(self, document_id: str) -> Optional[ProcessedDocument]:
        """
        Process an uploaded document through Docling.
        
        Args:
            document_id: ID of the uploaded document
            
        Returns:
            ProcessedDocument with structured content, or None if failed
        """
        # Find the uploaded file
        upload_dir = Path(self.settings.upload_directory)
        matching_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not matching_files:
            raise FileNotFoundError(f"Document {document_id} not found in uploads")
        
        file_path = matching_files[0]
        file_type = file_path.suffix.lstrip(".")
        
        # Process through Docling
        result = self.converter.convert(str(file_path))
        doc = result.document
        
        # Extract metadata
        title = self._extract_title(doc, file_path.stem)
        authors = self._extract_authors(doc)
        date = self._extract_date(doc)
        
        # Get markdown content for RAG
        content = doc.export_to_markdown()
        
        # Save processed content
        processed_path = Path(self.settings.processed_directory) / f"{document_id}.md"
        processed_path.write_text(content)
        
        return ProcessedDocument(
            id=document_id,
            filename=file_path.name,
            title=title,
            authors=authors,
            date=date,
            file_type=file_type,
            status=SourceStatus.PROCESSED,
            chunk_count=0,  # Updated after chunking
            content_preview=content[:500] if content else None,
            metadata={
                "original_path": str(file_path),
                "processed_path": str(processed_path),
                "page_count": getattr(doc, "page_count", None),
            },
            processed_at=datetime.utcnow(),
        )
    
    async def process_url(self, url: str) -> Optional[ProcessedDocument]:
        """
        Process a URL through Docling.
        
        Args:
            url: URL to fetch and process
            
        Returns:
            ProcessedDocument with structured content, or None if failed
        """
        document_id = str(uuid.uuid4())
        
        # Process URL through Docling
        result = self.converter.convert(url)
        doc = result.document
        
        # Extract metadata
        title = self._extract_title(doc, url)
        authors = self._extract_authors(doc)
        date = self._extract_date(doc)
        
        # Get markdown content
        content = doc.export_to_markdown()
        
        # Save processed content
        processed_path = Path(self.settings.processed_directory) / f"{document_id}.md"
        processed_path.write_text(content)
        
        return ProcessedDocument(
            id=document_id,
            filename=url,
            title=title,
            authors=authors,
            date=date,
            file_type="url",
            status=SourceStatus.PROCESSED,
            chunk_count=0,
            content_preview=content[:500] if content else None,
            metadata={
                "source_url": url,
                "processed_path": str(processed_path),
            },
            processed_at=datetime.utcnow(),
        )
    
    async def chunk_document(
        self, 
        document: ProcessedDocument
    ) -> list[DocumentChunk]:
        """
        Chunk a processed document for embedding.
        
        Uses token-based splitting with overlap for optimal RAG retrieval.
        
        Args:
            document: Processed document to chunk
            
        Returns:
            List of DocumentChunk objects ready for embedding
        """
        # Load processed content
        processed_path = document.metadata.get("processed_path")
        if not processed_path:
            raise ValueError(f"No processed content for document {document.id}")
        
        content = Path(processed_path).read_text()
        
        # Simple chunking strategy (can be enhanced with tiktoken)
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        chunks = []
        
        # Split into sentences first for cleaner boundaries
        sentences = self._split_into_sentences(content)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(DocumentChunk(
                    id=f"{document.id}_chunk_{chunk_index}",
                    document_id=document.id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    metadata={
                        "source_title": document.title,
                        "authors": document.authors,
                        "date": document.date,
                    },
                ))
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + sentence
            else:
                current_chunk += sentence
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                id=f"{document.id}_chunk_{chunk_index}",
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                metadata={
                    "source_title": document.title,
                    "authors": document.authors,
                    "date": document.date,
                },
            ))
        
        return chunks
    
    def _extract_title(self, doc, fallback: str) -> str:
        """Extract document title from Docling output."""
        # Try to get title from document metadata
        if hasattr(doc, "metadata") and doc.metadata:
            if hasattr(doc.metadata, "title") and doc.metadata.title:
                return doc.metadata.title
        
        # Try to get first heading
        if hasattr(doc, "headings") and doc.headings:
            return doc.headings[0].text if doc.headings[0].text else fallback
        
        return fallback
    
    def _extract_authors(self, doc) -> list[str]:
        """Extract authors from document metadata."""
        if hasattr(doc, "metadata") and doc.metadata:
            if hasattr(doc.metadata, "authors") and doc.metadata.authors:
                return doc.metadata.authors
        return []
    
    def _extract_date(self, doc) -> Optional[str]:
        """Extract publication date from document metadata."""
        if hasattr(doc, "metadata") and doc.metadata:
            if hasattr(doc.metadata, "date") and doc.metadata.date:
                return str(doc.metadata.date)
        return None
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences for cleaner chunking."""
        import re
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s + " " for s in sentences if s.strip()]
