"""Docling document processing service.

Handles conversion of arbitrary documents (PDF, DOCX, PPTX, images)
into structured, RAG-ready content using Docling.

Key features:
- Multi-format support via Docling's unified API
- Structured JSON/Markdown output
- Semantic chunking with overlap
- Metadata extraction (title, authors, date)
- Table and image handling
"""

import uuid
import re
import json
import logging
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from models.schemas import ProcessedDocument, DocumentChunk, SourceStatus
from config import get_settings

logger = logging.getLogger(__name__)


class DoclingService:
    """Service for document processing via Docling.
    
    Docling provides unified document conversion for:
    - PDF (with OCR fallback)
    - DOCX (Word documents)
    - PPTX (PowerPoint presentations)
    - HTML (web pages)
    - Images (PNG, JPG with OCR)
    
    Output is structured markdown/JSON preserving:
    - Document structure (headings, sections)
    - Tables (converted to markdown tables)
    - Images (extracted with captions)
    - Metadata (title, authors, dates)
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._converter = None
        self._pipeline_options = None
    
    @property
    def converter(self):
        """Lazy-load Docling converter with optimized settings."""
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                from docling.datamodel.base_models import InputFormat
                from docling.document_converter import PdfFormatOption
                
                # Configure pipeline for best quality
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = True  # Enable OCR for scanned PDFs
                pipeline_options.do_table_structure = True  # Extract tables
                
                self._converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
                logger.info("Docling DocumentConverter initialized successfully")
            except ImportError as e:
                logger.warning(f"Docling import error: {e}. Using fallback converter.")
                self._converter = FallbackConverter()
            except Exception as e:
                logger.warning(f"Docling initialization error: {e}. Using fallback converter.")
                self._converter = FallbackConverter()
        
        return self._converter
    
    async def process_document(self, document_id: str) -> Optional[ProcessedDocument]:
        """
        Process an uploaded document through Docling.
        
        Pipeline:
        1. Locate uploaded file by document_id
        2. Convert via Docling to structured format
        3. Extract metadata (title, authors, date)
        4. Export to Markdown and JSON
        5. Save processed content
        
        Args:
            document_id: ID of the uploaded document
            
        Returns:
            ProcessedDocument with structured content and metadata
            
        Raises:
            FileNotFoundError: If document_id doesn't match any uploaded file
        """
        # Find the uploaded file
        upload_dir = Path(self.settings.upload_directory)
        upload_dir.mkdir(parents=True, exist_ok=True)
        matching_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not matching_files:
            raise FileNotFoundError(f"Document {document_id} not found in uploads directory")
        
        file_path = matching_files[0]
        file_type = file_path.suffix.lstrip(".").lower()
        original_filename = file_path.name
        
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Convert through Docling
            result = self.converter.convert(str(file_path))
            
            # Handle different Docling API versions
            if hasattr(result, 'document'):
                doc = result.document
            else:
                doc = result
            
            # Extract content as markdown
            if hasattr(doc, 'export_to_markdown'):
                markdown_content = doc.export_to_markdown()
            elif hasattr(result, 'markdown'):
                markdown_content = result.markdown
            else:
                # Fallback: read file content directly for text-based formats
                markdown_content = self._extract_content_fallback(file_path, file_type)
            
            # Extract structured JSON if available
            json_content = None
            if hasattr(doc, 'export_to_dict'):
                json_content = doc.export_to_dict()
            elif hasattr(result, 'to_dict'):
                json_content = result.to_dict()
            
            # Extract metadata
            title = self._extract_title(doc, result, file_path.stem, markdown_content)
            authors = self._extract_authors(doc, result)
            date = self._extract_date(doc, result)
            page_count = self._extract_page_count(doc, result)
            
            # Ensure processed directory exists
            processed_dir = Path(self.settings.processed_directory)
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Save processed content
            md_path = processed_dir / f"{document_id}.md"
            md_path.write_text(markdown_content, encoding='utf-8')
            
            json_path = None
            if json_content:
                json_path = processed_dir / f"{document_id}.json"
                json_path.write_text(json.dumps(json_content, indent=2, default=str), encoding='utf-8')
            
            logger.info(f"Document processed successfully: {title} ({len(markdown_content)} chars)")
            
            return ProcessedDocument(
                id=document_id,
                filename=original_filename,
                title=title,
                authors=authors,
                date=date,
                file_type=file_type,
                status=SourceStatus.PROCESSED,
                chunk_count=0,  # Updated after chunking
                content_preview=markdown_content[:500] if markdown_content else None,
                metadata={
                    "original_path": str(file_path),
                    "processed_md_path": str(md_path),
                    "processed_json_path": str(json_path) if json_path else None,
                    "page_count": page_count,
                    "content_length": len(markdown_content),
                    "has_tables": "| " in markdown_content,  # Simple table detection
                    "has_images": "![" in markdown_content,  # Simple image detection
                },
                processed_at=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            raise
    
    async def process_url(self, url: str) -> Optional[ProcessedDocument]:
        """
        Process a URL through Docling.
        
        Supports:
        - Direct PDF links
        - HTML web pages
        - Academic paper URLs (arXiv, PubMed, etc.)
        
        Args:
            url: URL to fetch and process
            
        Returns:
            ProcessedDocument with structured content
        """
        document_id = str(uuid.uuid4())
        
        logger.info(f"Processing URL: {url}")
        
        try:
            # Process URL through Docling
            result = self.converter.convert(url)
            
            # Handle different Docling API versions
            if hasattr(result, 'document'):
                doc = result.document
            else:
                doc = result
            
            # Extract content
            if hasattr(doc, 'export_to_markdown'):
                markdown_content = doc.export_to_markdown()
            elif hasattr(result, 'markdown'):
                markdown_content = result.markdown
            else:
                markdown_content = f"# Content from {url}\n\nUnable to extract content."
            
            # Extract structured JSON if available
            json_content = None
            if hasattr(doc, 'export_to_dict'):
                json_content = doc.export_to_dict()
            
            # Extract metadata
            title = self._extract_title(doc, result, self._url_to_title(url), markdown_content)
            authors = self._extract_authors(doc, result)
            date = self._extract_date(doc, result)
            
            # Save processed content
            processed_dir = Path(self.settings.processed_directory)
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            md_path = processed_dir / f"{document_id}.md"
            md_path.write_text(markdown_content, encoding='utf-8')
            
            json_path = None
            if json_content:
                json_path = processed_dir / f"{document_id}.json"
                json_path.write_text(json.dumps(json_content, indent=2, default=str), encoding='utf-8')
            
            logger.info(f"URL processed successfully: {title}")
            
            return ProcessedDocument(
                id=document_id,
                filename=url,
                title=title,
                authors=authors,
                date=date,
                file_type="url",
                status=SourceStatus.PROCESSED,
                chunk_count=0,
                content_preview=markdown_content[:500] if markdown_content else None,
                metadata={
                    "source_url": url,
                    "processed_md_path": str(md_path),
                    "processed_json_path": str(json_path) if json_path else None,
                    "content_length": len(markdown_content),
                },
                processed_at=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            raise
    
    async def chunk_document(self, document: ProcessedDocument) -> list[DocumentChunk]:
        """
        Chunk a processed document for embedding.
        
        Uses semantic chunking strategy:
        1. Split by section headers (##, ###)
        2. Split by paragraphs within sections
        3. Ensure chunks respect sentence boundaries
        4. Apply overlap for context continuity
        
        Args:
            document: Processed document to chunk
            
        Returns:
            List of DocumentChunk objects ready for embedding
        """
        # Load processed content
        processed_path = document.metadata.get("processed_md_path") or document.metadata.get("processed_path")
        if not processed_path:
            raise ValueError(f"No processed content path for document {document.id}")
        
        content = Path(processed_path).read_text(encoding='utf-8')
        
        if not content.strip():
            logger.warning(f"Document {document.id} has empty content")
            return []
        
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        chunks = []
        chunk_index = 0
        
        # Strategy 1: Try to split by sections first
        sections = self._split_by_sections(content)
        
        for section in sections:
            section_chunks = self._chunk_text(
                text=section["content"],
                max_size=chunk_size,
                overlap=chunk_overlap,
                section_title=section.get("title"),
            )
            
            for chunk_content in section_chunks:
                if chunk_content.strip():
                    chunks.append(DocumentChunk(
                        id=f"{document.id}_chunk_{chunk_index}",
                        document_id=document.id,
                        content=chunk_content.strip(),
                        chunk_index=chunk_index,
                        metadata={
                            "source_title": document.title,
                            "authors": document.authors,
                            "date": document.date,
                            "section_title": section.get("title"),
                            "file_type": document.file_type,
                        },
                    ))
                    chunk_index += 1
        
        # Update document chunk count
        document.chunk_count = len(chunks)
        
        logger.info(f"Document {document.id} chunked into {len(chunks)} chunks")
        
        return chunks
    
    def _split_by_sections(self, content: str) -> list[dict]:
        """Split content by markdown headers into sections."""
        sections = []
        
        # Match markdown headers (## or ###)
        header_pattern = r'^(#{1,3})\s+(.+?)$'
        
        lines = content.split('\n')
        current_section = {"title": None, "content": ""}
        
        for line in lines:
            header_match = re.match(header_pattern, line, re.MULTILINE)
            
            if header_match:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": header_match.group(2).strip(),
                    "content": line + "\n"
                }
            else:
                current_section["content"] += line + "\n"
        
        # Don't forget the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        # If no sections found, treat entire content as one section
        if not sections:
            sections = [{"title": None, "content": content}]
        
        return sections
    
    def _chunk_text(
        self, 
        text: str, 
        max_size: int, 
        overlap: int,
        section_title: Optional[str] = None
    ) -> list[str]:
        """Chunk text respecting sentence boundaries."""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence exceeds max_size
            if len(current_chunk) + len(sentence) > max_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from previous
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + sentence
            else:
                current_chunk += sentence
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_chars: int) -> str:
        """Get overlap text from the end of previous chunk."""
        if len(text) <= overlap_chars:
            return text
        
        # Try to get overlap at sentence boundary
        overlap_text = text[-overlap_chars:]
        
        # Find first sentence start in overlap
        sentence_start = overlap_text.find('. ')
        if sentence_start > 0:
            return overlap_text[sentence_start + 2:]
        
        return overlap_text
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences with better boundary detection."""
        # Handle common abbreviations to avoid false splits
        text = text.replace('Dr.', 'Dr@')
        text = text.replace('Mr.', 'Mr@')
        text = text.replace('Mrs.', 'Mrs@')
        text = text.replace('Ms.', 'Ms@')
        text = text.replace('Prof.', 'Prof@')
        text = text.replace('et al.', 'et al@')
        text = text.replace('i.e.', 'i@e@')
        text = text.replace('e.g.', 'e@g@')
        text = text.replace('vs.', 'vs@')
        text = text.replace('Fig.', 'Fig@')
        text = text.replace('fig.', 'fig@')
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restore abbreviations and add space
        result = []
        for s in sentences:
            s = s.replace('@', '.')
            if s.strip():
                result.append(s + " ")
        
        return result
    
    def _extract_title(self, doc: Any, result: Any, fallback: str, content: str = "") -> str:
        """Extract document title from Docling output."""
        # Try Docling document object
        if hasattr(doc, 'name') and doc.name:
            return doc.name
        
        if hasattr(doc, 'metadata') and doc.metadata:
            if hasattr(doc.metadata, 'title') and doc.metadata.title:
                return doc.metadata.title
        
        # Try result object
        if hasattr(result, 'name') and result.name:
            return result.name
        
        # Try to extract from first heading in content
        if content:
            first_heading = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if first_heading:
                return first_heading.group(1).strip()
        
        # Clean up fallback (remove file extensions, underscores)
        clean_fallback = re.sub(r'\.[^.]+$', '', fallback)  # Remove extension
        clean_fallback = clean_fallback.replace('_', ' ').replace('-', ' ')
        clean_fallback = ' '.join(word.capitalize() for word in clean_fallback.split())
        
        return clean_fallback
    
    def _extract_authors(self, doc: Any, result: Any) -> list[str]:
        """Extract authors from document metadata."""
        if hasattr(doc, 'metadata') and doc.metadata:
            if hasattr(doc.metadata, 'authors') and doc.metadata.authors:
                authors = doc.metadata.authors
                if isinstance(authors, list):
                    return authors
                if isinstance(authors, str):
                    return [a.strip() for a in authors.split(',')]
        
        if hasattr(result, 'metadata') and result.metadata:
            if hasattr(result.metadata, 'authors'):
                return result.metadata.authors
        
        return []
    
    def _extract_date(self, doc: Any, result: Any) -> Optional[str]:
        """Extract publication date from document metadata."""
        if hasattr(doc, 'metadata') and doc.metadata:
            if hasattr(doc.metadata, 'date') and doc.metadata.date:
                return str(doc.metadata.date)
            if hasattr(doc.metadata, 'created') and doc.metadata.created:
                return str(doc.metadata.created)
        
        if hasattr(result, 'metadata') and result.metadata:
            if hasattr(result.metadata, 'date'):
                return str(result.metadata.date)
        
        return None
    
    def _extract_page_count(self, doc: Any, result: Any) -> Optional[int]:
        """Extract page count from document."""
        if hasattr(doc, 'page_count'):
            return doc.page_count
        if hasattr(doc, 'pages') and doc.pages:
            return len(doc.pages)
        if hasattr(result, 'page_count'):
            return result.page_count
        return None
    
    def _url_to_title(self, url: str) -> str:
        """Convert URL to a readable title."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # Extract meaningful part from path
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if path_parts:
            # Use last meaningful path segment
            title = path_parts[-1]
            # Clean up
            title = re.sub(r'\.[^.]+$', '', title)  # Remove extension
            title = title.replace('_', ' ').replace('-', ' ')
            return title.title()
        
        return parsed.netloc
    
    def _extract_content_fallback(self, file_path: Path, file_type: str) -> str:
        """Fallback content extraction when Docling fails."""
        try:
            if file_type in ['txt', 'md', 'markdown']:
                return file_path.read_text(encoding='utf-8')
            
            # For other formats, return placeholder
            return f"# Document: {file_path.stem}\n\nContent extraction pending. File type: {file_type}"
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return f"# Document: {file_path.stem}\n\nUnable to extract content."


class FallbackConverter:
    """Fallback converter when Docling is not available.
    
    Provides basic document reading capabilities without Docling.
    """
    
    def convert(self, source: str) -> 'FallbackResult':
        """Convert document using basic methods."""
        from pathlib import Path
        
        path = Path(source)
        
        if path.exists():
            # Local file
            file_type = path.suffix.lstrip('.').lower()
            
            if file_type in ['txt', 'md', 'markdown']:
                content = path.read_text(encoding='utf-8')
            elif file_type == 'pdf':
                content = self._extract_pdf(path)
            else:
                content = f"# {path.stem}\n\nFile type '{file_type}' requires Docling for proper extraction.\n\nPlease install Docling: `pip install docling`"
            
            return FallbackResult(
                name=path.stem,
                markdown=content,
            )
        else:
            # URL - try basic fetch
            content = self._fetch_url(source)
            return FallbackResult(
                name=source,
                markdown=content,
            )
    
    def _extract_pdf(self, path: Path) -> str:
        """Try to extract PDF text using PyPDF2 or pdfplumber."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n\n".join(text_parts)
        except ImportError:
            pass
        
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
                return "\n\n".join(text_parts)
        except ImportError:
            pass
        
        return f"# {path.stem}\n\nPDF extraction requires Docling or pypdf. Install with: `pip install docling` or `pip install pypdf`"
    
    def _fetch_url(self, url: str) -> str:
        """Fetch URL content."""
        try:
            import httpx
            response = httpx.get(url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            
            if 'html' in content_type:
                # Basic HTML to text
                from html.parser import HTMLParser
                
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip = False
                    
                    def handle_starttag(self, tag, attrs):
                        if tag in ['script', 'style', 'nav', 'footer']:
                            self.skip = True
                    
                    def handle_endtag(self, tag):
                        if tag in ['script', 'style', 'nav', 'footer']:
                            self.skip = False
                        if tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'li']:
                            self.text.append('\n')
                    
                    def handle_data(self, data):
                        if not self.skip:
                            self.text.append(data.strip())
                
                extractor = TextExtractor()
                extractor.feed(response.text)
                return ' '.join(extractor.text)
            
            return response.text
            
        except Exception as e:
            return f"# Error fetching URL\n\nFailed to fetch {url}: {str(e)}"


class FallbackResult:
    """Result object for fallback converter."""
    
    def __init__(self, name: str, markdown: str):
        self.name = name
        self.markdown = markdown
        self.document = self
    
    def export_to_markdown(self) -> str:
        return self.markdown
    
    def export_to_dict(self) -> dict:
        return {"name": self.name, "content": self.markdown}
